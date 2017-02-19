<?php

namespace edesarrollos\joom2wp;

use WP_CLI;
use WP_CLI\Utils;

class MigrateCommand extends \WP_CLI_Command {

	public function migrate($args=[], $assoc_args=[], $verbose=true) {

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

		$mysql = mysqli_connect(
			$assoc_args['db_host'],
			$assoc_args['db_user'],
			$assoc_args['db_pwd'],
			$assoc_args['db_name']
		);

		$categories = get_categories([
			'taxonomy' => $assoc_args['taxonomy']
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
	        	   i.catid, c.alias, i.created 
	        from {$tablePrefix}k2_items as i 
	        inner join {$tablePrefix}k2_categories as c 
	            on i.catid = c.id 
		");

		$mediaUtil = new \Media_Command;

		while ($row = $result->fetch_object()) {
			$md5ID = md5($row->id);
			$imagenURL = "{$joomlaURL}/media/k2/items/cache/{$md5ID}_XL.jpg";
			$postID = wp_insert_post([
				'post_title'   => $row->title,
				'post_content' => $row->fulltext,
				'post_excerpt' => $row->introtext,
				'post_type'    => $postType,
				'post_name'    => substr($row->alias, 0, 200),
				'post_date'    => $row->created
			]);
			
			$mediaUtil->import([$imagenURL], [
				'post_id' => $postID
			]);
		}
	}

}

WP_CLI::add_command('joom2wp posts', __NAMESPACE__ . '\\MigrateCommand');