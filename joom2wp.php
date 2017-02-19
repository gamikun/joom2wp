<?php

namespace edesarrollos\joom2wp;

use WP_CLI;

class MigrateCommand extends \WP_CLI_Command {

	public function migrate($args=[], $assoc_args=[], $verbose=true) {
		echo 'hola mundo';
	}

}

WP_CLI::add_command('joom2wp posts', __NAMESPACE__ . '\\MigrateCommand');