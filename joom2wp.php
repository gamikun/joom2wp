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
				'taxonomy' => 'category'
			]
		);

		$mysql = mysqli_connect(
			$assoc_args['db_host'],
			$assoc_args['db_user'],
			$assoc_args['db_pwd'],
			$assoc_args['db_name']
		);

		$categories = get_categories([
			'taxonomy' => $assoc_args['taxonomy']
		]);

		var_dump($categories);
	}

}

WP_CLI::add_command('joom2wp posts', __NAMESPACE__ . '\\MigrateCommand');