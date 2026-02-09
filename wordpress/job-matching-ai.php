<?php
/**
 * Plugin Name: Job Matching AI Embed
 * Plugin URI: https://github.com/yourusername/JobMatchingApp
 * Description: Embed the Job Matching AI application anywhere on your WordPress site using shortcodes.
 * Version: 1.0.0
 * Author: Your Name
 * License: MIT
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Register settings page
add_action('admin_menu', 'jmai_add_settings_page');

function jmai_add_settings_page() {
    add_options_page(
        'Job Matching AI Settings',
        'Job Matching AI',
        'manage_options',
        'job-matching-ai',
        'jmai_render_settings_page'
    );
}

function jmai_render_settings_page() {
    ?>
    <div class="wrap">
        <h1>🎯 Job Matching AI Settings</h1>
        <form method="post" action="options.php">
            <?php
            settings_fields('jmai_settings');
            do_settings_sections('jmai_settings');
            ?>
            <table class="form-table">
                <tr>
                    <th scope="row">Application URL</th>
                    <td>
                        <input type="url" name="jmai_app_url" value="<?php echo esc_attr(get_option('jmai_app_url', 'http://localhost:8501')); ?>" class="regular-text" />
                        <p class="description">Enter the URL where your Streamlit app is running.</p>
                    </td>
                </tr>
                <tr>
                    <th scope="row">Default Height</th>
                    <td>
                        <input type="text" name="jmai_default_height" value="<?php echo esc_attr(get_option('jmai_default_height', '850px')); ?>" class="small-text" />
                        <p class="description">Default iframe height (e.g., 850px, 100vh).</p>
                    </td>
                </tr>
                <tr>
                    <th scope="row">Enable Glassmorphism</th>
                    <td>
                        <input type="checkbox" name="jmai_enable_glass" value="1" <?php checked(get_option('jmai_enable_glass', '1'), '1'); ?> />
                        <label>Add glassmorphism frame around the embed</label>
                    </td>
                </tr>
            </table>
            <?php submit_button(); ?>
        </form>
        
        <hr>
        
        <h2>📋 Available Shortcodes</h2>
        <table class="wp-list-table widefat fixed striped">
            <thead>
                <tr>
                    <th>Shortcode</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><code>[job_matching_ai]</code></td>
                    <td>Embed with default settings</td>
                </tr>
                <tr>
                    <td><code>[job_matching_ai height="600px"]</code></td>
                    <td>Custom height</td>
                </tr>
                <tr>
                    <td><code>[job_matching_ai glass="false"]</code></td>
                    <td>Without glassmorphism frame</td>
                </tr>
                <tr>
                    <td><code>[job_matching_ai url="https://custom-url.com"]</code></td>
                    <td>Custom URL override</td>
                </tr>
            </tbody>
        </table>
    </div>
    <?php
}

// Register settings
add_action('admin_init', 'jmai_register_settings');

function jmai_register_settings() {
    register_setting('jmai_settings', 'jmai_app_url');
    register_setting('jmai_settings', 'jmai_default_height');
    register_setting('jmai_settings', 'jmai_enable_glass');
}

// Register shortcode
add_shortcode('job_matching_ai', 'jmai_shortcode');

function jmai_shortcode($atts) {
    $atts = shortcode_atts(array(
        'url' => get_option('jmai_app_url', 'http://localhost:8501'),
        'height' => get_option('jmai_default_height', '850px'),
        'glass' => get_option('jmai_enable_glass', '1') ? 'true' : 'false',
        'width' => '100%',
    ), $atts, 'job_matching_ai');
    
    $use_glass = ($atts['glass'] === 'true' || $atts['glass'] === '1');
    
    // Enqueue styles
    wp_enqueue_style('jmai-styles', plugins_url('jmai-styles.css', __FILE__));
    
    $iframe = sprintf(
        '<iframe src="%s" width="%s" height="%s" frameborder="0" allow="clipboard-write" loading="lazy" title="Job Matching AI" class="jmai-iframe"></iframe>',
        esc_url($atts['url']),
        esc_attr($atts['width']),
        esc_attr($atts['height'])
    );
    
    if ($use_glass) {
        return '<div class="jmai-glass-container">' . $iframe . '</div>';
    }
    
    return '<div class="jmai-container">' . $iframe . '</div>';
}

// Add inline styles as fallback
add_action('wp_head', 'jmai_inline_styles');

function jmai_inline_styles() {
    ?>
    <style>
    .jmai-container {
        width: 100%;
        max-width: 1400px;
        margin: 20px auto;
    }
    
    .jmai-container iframe,
    .jmai-glass-container iframe {
        width: 100%;
        border: none;
        border-radius: 16px;
        display: block;
    }
    
    .jmai-glass-container {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.25);
        border-radius: 24px;
        padding: 10px;
        box-shadow: 
            0 8px 32px rgba(0, 0, 0, 0.12),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
        max-width: 1400px;
        margin: 20px auto;
    }
    
    .jmai-glass-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        border-radius: 24px 24px 0 0;
    }
    
    @media (max-width: 768px) {
        .jmai-glass-container {
            border-radius: 16px;
            padding: 6px;
            margin: 10px;
        }
        
        .jmai-glass-container iframe,
        .jmai-container iframe {
            border-radius: 10px;
            height: 600px !important;
        }
    }
    </style>
    <?php
}
