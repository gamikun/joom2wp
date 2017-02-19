#!/usr/bin/python

from MySQLdb import connect
from hashlib import md5
from argparse import ArgumentParser
from datetime import datetime
import subprocess
import requests
import os
import StringIO
import csv


parser = ArgumentParser()
parser.add_argument('--db-host', help='Source database',
                    dest='db_host', nargs=2,
                    default='localhost')
parser.add_argument('--db-user', help='Database user',
                    dest='db_user',
                    default=['root', 'root'])
parser.add_argument('--db-name', help='Database name',
                    required=True, dest='db_name')
parser.add_argument('--db-pwd', help='Password', required=True,
                    dest='db_password')
parser.add_argument('--db-prefix', help='Tables prefixes',
                    required=True, dest='table_prefix',
                    default='jo_')
parser.add_argument('-p', help='Post type to be inserted',
                    dest='post_type', default='post')
parser.add_argument('-u', help='Joomla URL', dest='joomla_url', default=None)
parser.add_argument('-d', help='Destination Base URL',
                    required=True, dest='destination_url')
parser.add_argument('-c', help='Commit changes to database.',
                    action='store_const', const=True, dest='commit')
parser.add_argument('--revert', help='Do a database revert with the inserted posts',
                    action='store_const', const=True, dest='do_revert')
parser.add_argument('-t', help='Replace taxonomy',
                    dest='category_taxonomy',
                    default='category',
                    type=str
                    )

args = parser.parse_args()


k2_prefix = args.table_prefix
source = connect(host=args.db_host,
		 user=args.db_user,
		 db=args.db_name,
		 passwd=args.db_password
		 )

images_path = '/var/www/the-emag/wp-content/uploads/migrated'

scursor = source.cursor()

""" Wordpress categories """
wp_cats = {}
cat_taxonomy = args.category_taxonomy
raw_cats = subprocess.check_output([
    'wp', 'term', 'list', cat_taxonomy,
    '--format=csv',
    '--fields=slug,term_id,name,term_taxonomy_id'
])

for cat in csv.reader(StringIO.StringIO(raw_cats)):
    slug, cid, name, tx_id = cat
    wp_cats[slug] = (cid, name, tx_id, )


""" Joomla Categories list """
cats = {}
scursor.execute(
    "select id, alias, name from {}k2_categories"\
        .format(args.table_prefix)
)
for cat in scursor:
    cid, alias, title = cat
    cats[cid] = (alias, title, )


if not args.do_revert:

    """ K2 Items """
    query = """
        select i.id, i.title, i.alias, i.`fulltext`,
               i.introtext, i.catid, c.alias, i.created
        from {0}k2_items as i
        inner join {0}k2_categories as c
            on i.catid = c.id
        """
    preapred_query = query.format(args.table_prefix)
    scursor.execute(preapred_query)

    def insert_media(theid, url, post_id=None):
        try:
            subprocess.check_call([
                'wp', 'media', 'import', url,
                '--post_mime_type="image/jpeg"',
                '--post_type="attachment"',
                '--featured_image',
                '--post_id={}'.format(post_id)
            ])
        except Exception as ex:
            print(ex)
            raise

    def insert_category(name, slug):
        term_id = int(subprocess.call([
            'wp', 'term', 'create',
            cat_taxonomy, name,
            '--description="{}"'.format(name.replace('"', r'\"')),
            '--slug="{}"'.format(slug.replace('"', r'\"')),
            '--porcelain'
        ]))

        return term_id

    for row in scursor:
        theid, title, slug, \
            content, excerpt, \
            catid, catslug, created = row

        if catslug in wp_cats:
            the_cat_id, _, the_tax_id  = wp_cats[catslug]
        elif catid in cats:
            cat_slug, cat_title = cats[catid]
            the_cat_id = insert_category(cat_title, cat_slug)
            wp_cats[cat_slug] = (the_cat_id, cat_slug, )
        else:
            the_cat_id = None

        delta = created - datetime.fromtimestamp(0)
        timestmap = int(delta.total_seconds())

        post_id = int(subprocess.check_output("""
            wp post create\ 
            --post_title="{}" \
            --post_name="{}" \
            --post_content="{}" \
            --post_excerpt="{}" \
            --post_type="{}" \
            --post_date="{:%Y-%m-%d %H:%M:%S}" \
            --porcelain
            """.format(
                title.replace('"', r'\"'),
                slug[:200].replace('"', r'\"'),
                content.replace('"', r'\"'),
                excerpt,
                args.post_type,
                created
            )
        ], shell=True))

        md5id = md5("Image" + str(theid)).hexdigest()
        filename = md5id + '.jpg'
        image_url = '{}/media/k2/items/cache/{}_XL.jpg'.format(args.joomla_url, md5id)

      

else:
    tcursor.execute("""
        delete from wp_posts
        where post_type = 'attachment'
        and guid like '%migrated%';
    """)
    tcursor.execute("""
        delete from wp_posts
        where post_type = 'post_colombia';
    """)



    