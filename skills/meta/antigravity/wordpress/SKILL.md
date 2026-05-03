     1|---
     2|name: ag-wordpress
     3|description: "Complete WordPress development workflow covering theme development, plugin creation, WooCommerce integration, performance optimization, and security h"
     4|version: 1.0.0
     5|tags: [antigravity, security]
     6|category: software-development
     7|source: https://github.com/sickn33/antigravity-awesome-skills
     8|---
     9|
    10|---
    11|name: wordpress
    12|description: "Complete WordPress development workflow covering theme development, plugin creation, WooCommerce integration, performance optimization, and security hardening. Includes WordPress 7.0 features: Real-Time Collaboration, AI Connectors, Abilities API, DataViews, and PHP-only blocks."
    13|category: workflow-bundle
    14|risk: safe
    15|source: personal
    16|date_added: "2026-02-27"
    17|---
    18|
    19|# WordPress Development Workflow Bundle
    20|
    21|## Overview
    22|
    23|Comprehensive WordPress development workflow covering theme development, plugin creation, WooCommerce integration, performance optimization, and security. This bundle orchestrates skills for building production-ready WordPress sites and applications.
    24|
    25|## WordPress 7.0 Features (Backward Compatible)
    26|
    27|WordPress 7.0 (April 9, 2026) introduces significant features while maintaining backward compatibility:
    28|
    29|### Real-Time Collaboration (RTC)
    30|- Multiple users can edit simultaneously using Yjs CRDT
    31|- HTTP polling provider (configurable via `WP_COLLABORATION_MAX_USERS`)
    32|- Custom transport via `sync.providers` filter
    33|- **Backward Compatibility**: Falls back to post locking when legacy meta boxes detected
    34|
    35|### AI Connectors API
    36|- Provider-agnostic AI interface in core (`wp_ai_client_prompt()`)
    37|- Settings > Connectors for centralized API credential management
    38|- Official providers: OpenAI, Anthropic Claude, Google Gemini
    39|- **Backward Compatibility**: Works with WordPress 6.9+ via plugin
    40|
    41|### Abilities API (Stable in 7.0)
    42|- Standardized capability declaration system
    43|- REST API endpoints: `/wp-json/abilities/v1/manifest`
    44|- MCP adapter for AI agent integration
    45|- **Backward Compatibility**: Can be used as Composer package in 6.x
    46|
    47|### DataViews & DataForm
    48|- Replaces WP_List_Table on Posts, Pages, Media screens
    49|- New layouts: table, grid, list, activity
    50|- Client-side validation (pattern, minLength, maxLength, min, max)
    51|- **Backward Compatibility**: Plugins using old hooks still work
    52|
    53|### PHP-Only Block Registration
    54|- Register blocks entirely via PHP without JavaScript
    55|- Auto-generated Inspector controls
    56|- **Backward Compatibility**: Existing JS blocks continue to work
    57|
    58|### Interactivity API Updates
    59|- `watch()` replaces `effect` from @preact/signals
    60|- State navigation changes
    61|- **Backward Compatibility**: Old syntax deprecated but functional
    62|
    63|### Admin Refresh
    64|- New default color scheme
    65|- View transitions between admin screens
    66|- **Backward Compatibility**: CSS-level changes, no breaking changes
    67|
    68|### Pattern Editing
    69|- ContentOnly mode defaults for unsynced patterns
    70|- `disableContentOnlyForUnsyncedPatterns` setting
    71|- **Backward Compatibility**: Existing patterns work
    72|
    73|## When to Use This Workflow
    74|
    75|Use this workflow when:
    76|- Building new WordPress websites
    77|- Creating custom themes
    78|- Developing WordPress plugins
    79|- Setting up WooCommerce stores
    80|- Optimizing WordPress performance
    81|- Hardening WordPress security
    82|- Implementing WordPress 7.0 features (RTC, AI, DataViews)
    83|
    84|## Workflow Phases
    85|
    86|### Phase 1: WordPress Setup
    87|
    88|#### Skills to Invoke
    89|- `app-builder` - Project scaffolding
    90|- `environment-setup-guide` - Development environment
    91|
    92|#### Actions
    93|1. Set up local development environment (LocalWP, Docker, or Valet)
    94|2. Install WordPress (recommend 7.0+ for new projects)
    95|3. Configure development database
    96|4. Set up version control
    97|5. Configure wp-config.php for development
    98|
    99|#### WordPress 7.0 Configuration
   100|```php
   101|// wp-config.php - Collaboration settings
   102|define('WP_COLLABORATION_MAX_USERS', 5);
   103|
   104|// AI Connector is enabled by installing a provider plugin
   105|// (e.g., OpenAI, Anthropic Claude, or Google Gemini connector)
   106|// No constant needed - configure via Settings > Connectors in admin
   107|```
   108|
   109|#### Copy-Paste Prompts
   110|```
   111|Use @app-builder to scaffold a new WordPress project with modern tooling
   112|```
   113|
   114|### Phase 2: Theme Development
   115|
   116|#### Skills to Invoke
   117|- `frontend-developer` - Component development
   118|- `frontend-design` - UI implementation
   119|- `tailwind-patterns` - Styling
   120|- `web-performance-optimization` - Performance
   121|
   122|#### Actions
   123|1. Design theme architecture
   124|2. Create theme files (style.css, functions.php, index.php)
   125|3. Implement template hierarchy
   126|4. Create custom page templates
   127|5. Add custom post types and taxonomies
   128|6. Implement theme customization options
   129|7. Add responsive design
   130|8. Test with WordPress 7.0 admin refresh
   131|
   132|#### WordPress 7.0 Theme Considerations
   133|- Block API v3 now reference model
   134|- Pseudo-element support in theme.json
   135|- Global Styles custom CSS honors block-defined selectors
   136|- View transitions for admin navigation
   137|
   138|#### Theme Structure
   139|```
   140|theme-name/
   141|├── style.css
   142|├── functions.php
   143|├── index.php
   144|├── header.php
   145|├── footer.php
   146|├── sidebar.php
   147|├── single.php
   148|├── page.php
   149|├── archive.php
   150|├── search.php
   151|├── 404.php
   152|├── template-parts/
   153|├── inc/
   154|├── assets/
   155|│   ├── css/
   156|│   ├── js/
   157|│   └── images/
   158|└── languages/
   159|```
   160|
   161|#### Copy-Paste Prompts
   162|```
   163|Use @frontend-developer to create a custom WordPress theme with React components
   164|```
   165|
   166|```
   167|Use @tailwind-patterns to style WordPress theme with modern CSS
   168|```
   169|
   170|### Phase 3: Plugin Development
   171|
   172|#### Skills to Invoke
   173|- `backend-dev-guidelines` - Backend standards
   174|- `api-design-principles` - API design
   175|- `auth-implementation-patterns` - Authentication
   176|
   177|#### Actions
   178|1. Design plugin architecture
   179|2. Create plugin boilerplate
   180|3. Implement hooks (actions and filters)
   181|4. Create admin interfaces
   182|5. Add custom database tables
   183|6. Implement REST API endpoints
   184|7. Add settings and options pages
   185|
   186|#### WordPress 7.0 Plugin Considerations
   187|- **RTC Compatibility**: Register post meta with `show_in_rest => true`
   188|- **AI Integration**: Use `wp_ai_client_prompt()` for AI features
   189|- **DataViews**: Consider new admin UI patterns
   190|- **Meta Boxes**: Migrate to block-based UIs for collaboration support
   191|
   192|#### RTC-Compatible Post Meta Registration
   193|```php
   194|register_post_meta('post', 'custom_field', [
   195|    'type' => 'string',
   196|    'single' => true,
   197|    'show_in_rest' => true,  // Required for RTC
   198|    'sanitize_callback' => 'sanitize_text_field',
   199|]);
   200|```
   201|
   202|#### AI Connector Example
   203|```php
   204|// Using WordPress 7.0 AI Connector
   205|// Note: Requires an AI provider plugin (OpenAI, Claude, or Gemini) to be installed and configured
   206|
   207|// Basic text generation
   208|$response = wp_ai_client_prompt('Summarize this content.')
   209|    ->generate_text();
   210|