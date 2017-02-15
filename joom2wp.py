#!/usr/bin/python

from MySQLdb import connect
from hashlib import md5
from argparse import ArgumentParser
import requests
import os


parser = ArgumentParser()
parser.add_argument('--db-host', help='Source database', required=True, dest='db_host', nargs=2)
parser.add_argument('--db-user', help='database user', required=True, dest='db_user', nargs=2)
parser.add_argument('--db-name', help='Database name', required=True, dest='db_name', nargs=2)
parser.add_argument('--db-pwd', help='Password', required=True, dest='db_password', nargs=2)
parser.add_argument('--db-prefix', help='Tables prefixes', required=True, dest='table_prefix', nargs=2, default=('jo_', 'wp_'))
parser.add_argument('-p', help='Post type to be inserted', dest='post_type', default='post')
parser.add_argument('-u', help='Joomla URL', dest='joomla_url', default=None)
parser.add_argument('-d', help='Destination Base URL', required=True, dest='destination_url')
args = parser.parse_args()

source_prefix = args.table_prefix[0]
k2_prefix = args.table_prefix[0]
source = connect(host=args.db_host[0],
		 user=args.db_user[0],
		 db=args.db_name[0],
		 passwd=args.db_password[0]
		 )
target = connect(host=args.db_host[1],
                 user=args.db_user[1],
                 db=args.db_name[1],
                 passwd=args.db_password[1]
                 )

images_path = '/var/www/the-emag/wp-content/uploads/migrated'

scursor = source.cursor()
tcursor = target.cursor()

""" Wordpress categories """
wp_cats = {}
scursor = scursor.execute("""
    select slug, id, name 
    from wp_terms
    where term_group = 0
""")
for cat in scursor:
    slug, cid, name = cat
    wp_cats[slug] = (cid, name, )

""" Joomla Categories list """
cats = {}
scursor.execute("select id, alias, title from categories")
for cat in scursor:
    cid, alias, title = cat
    cats[cid] = (alias, title, )

""" K2 Items """
query = """
    select id, title, alias, `fulltext`,
           introtext, catid
    from {}k2_items i
    """
preapred_query = query.format(source_prefix)
scursor.execute(preapred_query)

def insert_media(theid, url):
    tcursor.execute("""
        insert into {}posts (
            ID, post_title, post_name, post_content,
            post_excerpt, to_ping, pinged, post_content_filtered,
            post_type, guid, post_mime_type
        )
        values (
            %s, '', '', '', '', '', '',
            '', 'attachment', %s, 'image/jpeg'
        );
        """.format(args.table_prefix[1]),
        (theid, url, )
    )  

def insert_category(name, slug):
    tcursor.execute("""
        insert into {}terms (
            name, slug, term_group
        )
        values (
            %s, %s, 0
        )
        """.format(args.table_prefix[1]), 
        (name, slug,)
    )
    return tcursor.lastrowid

for row in scursor:
    theid, title, slug, \
        content, excerpt, \
        catid = row
    print(theid)

    if args.joomla_url:
        md5id = md5("Image" + str(theid)).hexdigest()
        filename = md5id + '.jpg'
        image_url = '{}/media/k2/items/cache/{}_XL.jpg'.format(args.joomla_url, md5id)
        destination_url = os.path.join(args.destination_url, 'wp-content/uploads/migrated', filename)
        image_path = '{}/{}'.format(images_path, filename)
        if not os.path.isfile(image_path):
            response = requests.get(image_url)
            if response.status_code == 200:
                with open(image_path, 'wb') as fp:
                    fp.write(response.content)
                insert_media(200000 + theid, destination_url)
        else:
            insert_media(200000 + theid, destination_url)

    media_id = tcursor.lastrowid

    if catid in wp_cats:
        the_cat_id, _,  = wp_cats[catid]
    else:
        cat_slug, cat_title = cats[catid]
        the_cat_id = insert_category(cat_title, cat_slug)
        wp_cats[cat_slug] = (the_cat_id, cat_slug, )

    tcursor.execute("""
        insert into {}posts (
            post_title, post_name, post_content,
            post_excerpt, to_ping, pinged, post_content_filtered,
            post_type
        )
        values (%s, %s, %s, %s, '', '', '', %s)
    """.format(args.table_prefix[1]),
        (
            title,
            slug[:200], content, 
            excerpt, args.post_type
        )
    )

    post_id = tcursor.lastrowid

    if post_id and media_id:
        tcursor.execute("""
            insert into {}postmeta (
                post_id, meta_key, meta_value
            )
            values (%s, '_thumbnail_id', %s)
            """.format(args.table_prefix[1]),
            (post_id, media_id, )
        )       

#target.commit()


