<?php

namespace edesarrollos\joom2wp;

use WP_CLI;
use WP_CLI\Utils;

class MigrateCommand extends \WP_CLI_Command {

    public function migrate($args=[], $assoc_args=[], $verbose=true) {

        global $wpdb;
        $wpdb->show_errors();

        $allArgs = wp_parse_args(
            $assoc_args,
            [
                'db_host'  => 'localhost',
                'db_user'  => 'root',
                'post_type'=> 'post',
                'taxonomy' => 'category',
                'table_prefix' => 'jo_'
            ]
        );

        $postType = $allArgs['post_type'];
        $tablePrefix = $allArgs['table_prefix'];
        $joomlaURL = $allArgs['joomla_url'];
        $taxonomy = $allArgs['taxonomy'];

        $mysql = mysqli_connect(
            $allArgs['db_host'],
            $allArgs['db_user'],
            $allArgs['db_pwd'],
            $allArgs['db_name']
        );

        $categories = get_categories([
            'taxonomy' => $taxonomy
        ]);

        // WORDPRESS CATEGORIES

        $wp_cats = [];

        foreach ($categories as $cat) {
            $wp_cats[$cat->term_id] = $cat;
        }

        // JOOMLA CATEGORIES
        $cats = [];

        $result = $mysql->query("
            select id, alias, name
            from {$tablePrefix}k2_categories
        ");

        while ($row = $result->fetch_object()) {
            $cats[$row->id] = $row;
        }

        // JOOMLA K2
        $result = $mysql->query("
            select i.id, i.title, i.alias, 
                   i.`fulltext`, i.introtext, 
                   i.catid, c.alias, i.created,
                   c.name as catname,
                   u.username, u.userID,
                   u.email, u.name as userFullName,
                   u.registerDate
            from {$tablePrefix}k2_items as i 
            inner join {$tablePrefix}k2_categories as c 
                on i.catid = c.id
            left join {$tablePrefix}users as u
                on i.created_by = u.id
        ");

        if (!$result) {
            var_dump($mysql->error);
            WP_CLI::halt(1);
        }

        $mediaUtil = new \Media_Command;

        while ($row = $result->fetch_object()) {
            $catID = wp_create_category($row->catname);

            var_dump($authorID);

            $postParams = [
                'post_title'   => utf8_encode($row->title),
                'post_content' => utf8_encode($row->fulltext),
                'post_excerpt' => utf8_encode($row->introtext),
                'post_type'    => $postType,
                'post_name'    => utf8_encode(substr($row->alias, 0, 200)),
                'post_date'    => $row->created,
                'post_category'=> [$catID],
                'post_status'  => 'publish'
            ];

            if ($row->userID) {
                $user = get_user_by('user_login', utf8_encode($row->username));

                if (!$user) {
                    $authorID = wp_insert_user([
                        'user_login' => utf8_encode($row->username),
                        'display_name' => utf8_encode($row->userFullName),
                        'user_nicename' => utf8_encode($row->username),
                        'user_email' => utf8_encode($row->email),
                        'user_registered' => utf8_encode($row->registerDate)
                    ]);
                    WP_CLI::log("Registered user {$row->username}");
                } else {
                    $authorID = $user->ID;
                }

                $postParams['post_author']  => $authorID;
            }

            $postID = wp_insert_post($postParams);

            if ($postID) {
                WP_CLI::log("Imported post {$postID}");

                $md5ID = md5("Image" . $row->id);
                $imagenURL = "{$joomlaURL}/media/k2/items/cache/{$md5ID}_XL.jpg";

                $mediaUtil->import([$imagenURL], [
                    'post_id' => $postID,
                    'featured_image' => true,
                    'porcelain' => true
                ]);
            
            } else {
                WP_CLI::log("Couldn't import post.");
            }
        }
    }

}

WP_CLI::add_command('joom2wp posts', __NAMESPACE__ . '\\MigrateCommand');