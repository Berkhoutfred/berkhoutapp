<?php
/**
 * Plugin Name: Berkhout Mobile Menu Fix
 * Description: Corrigeert afgesneden menu-tekst in het Astra mobiele hamburger-menu op berkhoutreizen.nl.
 * Version: 1.0.1
 * Author: Berkhout
 */

declare(strict_types=1);

add_action(
	'wp_enqueue_scripts',
	static function (): void {
		$handle = 'berkhout-mobile-menu-fix';

		wp_register_style( $handle, false, array(), '1.0.1' );
		wp_enqueue_style( $handle );

		wp_add_inline_style(
			$handle,
			'@media (max-width:921px){'
			. '#ast-mobile-header .main-header-menu,'
			. '#ast-hf-menu-1-mobile.main-header-menu,'
			. '.ast-mobile-header-content .ast-builder-menu-1 .main-header-menu,'
			. '.ast-header-break-point .ast-builder-menu-1 .main-header-menu{'
			. 'margin:0!important;width:100%!important;max-width:100%!important;'
			. '}'
			. '.ast-mobile-header-content .main-header-menu .menu-item>.menu-link{'
			. 'padding:16px 20px!important;'
			. '}'
			. '.ast-mobile-header-content .menu-item.menu-item-has-children>.ast-menu-toggle{'
			. 'right:16px!important;top:50%!important;transform:translateY(-50%)!important;'
			. '}'
			. '.ast-mobile-header-content .sub-menu{'
			. 'width:100%!important;max-width:100%!important;position:static!important;'
			. 'border-width:0!important;box-shadow:none!important;'
			. '}'
			. '}'
		);
	},
	999
);
