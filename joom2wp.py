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

""" K2 Items """
scursor.execute("""
    select id, title, alias, `fulltext`, introtext
    from {}k2_items
""".format(source_prefix))

def insert_media(theid, url, postid):
    tcursor.execute("""
        insert into {}posts (
            ID, post_title, post_name, post_content,
            post_excerpt, to_ping, pinged, post_content_filtered,
            post_type, guid, post_mime_type
        )
        values (
            %s, '', '', '', '', '', '', 'attachment', %s, 'image/jpeg'
        );
        """,
        (theid, url, )
    )  

for row in scursor:
    theid, title, slug, content, excerpt = row
    print(theid)
    tcursor.execute("""
        insert into {}posts (
            ID, post_title, post_name, post_content,
            post_excerpt, to_ping, pinged, post_content_filtered,
            post_type
        )
        values (%s, %s, %s, %s, %s, '', '', '', %s);
        insert into {}postmeta (
            post_id, meta_key, meta_id
        )
        values ()
    """.format(args.table_prefix[1], args.table_prefix[1])
        (1000000 + theid, 'NOOOO_' + title,
         slug[:200], content, 
         excerpt, args.post_type
         )
    )
    
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
            print(destination_url)
            insert_media(200000 + theid, destination_url)

            

#target.commit()


