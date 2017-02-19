<?php

namespace edesarrollos\joom2wp;

use WP_CLI;

class MigrateCommand extends \WP_CLI_Command {

	public function migrate($args=[], $assoc_args=[], $verbose=true) {

		$this->assoc_args = wp_parse_args(
			$assoc_args,
			[
				'db_host'  => 'localhost',
				'db_user'  => 'root',
				'post_type'=> 'post',
				'taxonomy' => 'category',
				'table_prefix' => 'jo_'
			]
		);

		$tablePrefix = $assoc_args['table_prefix'];

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
	        inner join {tablePrefix}k2_categories as c 
	            on i.catid = c.id 
		");

		while ($row = $result->fetch_object()) {
			echo $row->id;
		}
	}

}

WP_CLI::add_command('joom2wp posts', __NAMESPACE__ . '\\MigrateCommand');