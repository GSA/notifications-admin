const baseUrl = process.env.BACKSTOP_BASE_URL || 'http://localhost:6012';

const TEST_SERVICE_ID = 'da14b8fa-6a9e-4320-8484-9cd6e900c333';
const TEST_TEMPLATE_ID = '31588995-646b-40ae-bed1-617612d9245e';
const TEST_USER_ID = '6af522d0-2915-4e52-83a3-3690455a5fe6';
const TEST_ORG_ID = 'a134fb9b-ab87-4e76-b216-77cb66a6ee18';

const servicePath = (path = '') => `/services/${TEST_SERVICE_ID}${path}`;
const userPath = (path = '') => `/user-profile${path}`;
const platformAdminPath = (path = '') => `/platform-admin${path}`;
const orgPath = (path = '') => `/organizations/${TEST_ORG_ID}${path}`;

const routes = {
  public: [
    { label: 'Homepage', path: '/' },
    { label: 'Support', path: '/support' },
    { label: 'Sign In', path: '/sign-in' },
    { label: 'Sign Out', path: '/sign-out' },
    { label: 'Forgot Password', path: '/forgot-password' },
    { label: 'Add Service', path: '/add-service' },
    { label: 'Contact', path: '/contact' },
    { label: 'Studio', path: '/studio' },
    { label: 'Privacy', path: '/privacy' },
    { label: 'Accessibility Statement', path: '/accessibility-statement' },
    { label: 'Performance', path: '/performance' },
    { label: 'Service Ending', path: '/notify-service-ending' },
    { label: 'Email Not Received', path: '/email-not-received' },
    { label: 'Text Not Received', path: '/text-not-received' },
    { label: 'Find Users', path: '/find-users-by-email' },
    { label: 'Find Services', path: '/find-services-by-name' },
  ],

  errors: [
    { label: 'Error 403', path: '/error/403' },
    { label: 'Error 404', path: '/error/404' },
  ],

  service: [
    { label: 'Service Dashboard', path: servicePath() },
    { label: 'Service Usage', path: servicePath('/usage') },
    { label: 'Service Template Usage', path: servicePath('/template-usage') },
    { label: 'Service Jobs', path: servicePath('/jobs') },
    { label: 'Service History', path: servicePath('/history') },
    { label: 'Service Settings', path: servicePath('/service-settings') },
    { label: 'Service Settings Admin', path: servicePath('/service-settings?show_admin_view=true') },
    { label: 'Choose Template', path: servicePath('/templates') },
    { label: 'Team Members', path: servicePath('/users') },
    { label: 'Invite User', path: servicePath('/users/invite') },
    { label: 'All Activity', path: `/activity${servicePath()}` },
    { label: 'Uploads', path: servicePath('/uploads') },
  ],

  serviceSettings: [
    { label: 'SMS Prefix', path: servicePath('/service-settings/sms-prefix') },
    { label: 'Send Files by Email', path: servicePath('/service-settings/send-files-by-email') },
    { label: 'Data Retention', path: servicePath('/data-retention') },
    { label: 'Data Retention Add', path: servicePath('/data-retention/add') },
    { label: 'Edit Billing Details', path: servicePath('/edit-billing-details') },
    { label: 'Edit Notes', path: servicePath('/notes') },
    { label: 'Link to Organization', path: servicePath('/service-settings/link-service-to-organization') },
  ],

  templates: [
    { label: 'Template View', path: servicePath(`/templates/${TEST_TEMPLATE_ID}`) },
    { label: 'Template Versions', path: servicePath(`/templates/${TEST_TEMPLATE_ID}/versions`) },
    { label: 'Template Copy', path: servicePath('/templates/copy') },
    { label: 'Template Preview', path: servicePath(`/send/${TEST_TEMPLATE_ID}/one-off/step-0`) },
    { label: 'Template Send Step 2', path: servicePath(`/send/${TEST_TEMPLATE_ID}/one-off/step-2`) },
    { label: 'Set Template Sender', path: servicePath(`/send/${TEST_TEMPLATE_ID}/set-sender`) },
    { label: 'Set Template Letter Sender', path: servicePath(`/templates/${TEST_TEMPLATE_ID}/set-template-sender`) },
  ],

  api: [
    { label: 'API Keys', path: servicePath('/api/keys') },
    { label: 'API Keys Create', path: servicePath('/api/keys/create') },
    { label: 'API Documentation', path: servicePath('/api/documentation') },
    { label: 'API Callbacks', path: servicePath('/api/callbacks') },
    { label: 'API Guest List', path: servicePath('/api/guest-list') },
  ],

  userProfile: [
    { label: 'User Profile', path: userPath() },
    { label: 'User Profile Name', path: userPath('/name') },
    { label: 'User Profile Email', path: userPath('/email') },
    { label: 'User Profile Mobile', path: userPath('/mobile-number') },
    { label: 'User Profile Password', path: userPath('/password') },
    { label: 'User Profile Timezone', path: userPath('/preferred_timezone') },
    { label: 'Change User Auth', path: `/users/${TEST_USER_ID}/change_auth` },
  ],

  organizations: [
    { label: 'Organizations List', path: '/organizations' },
    { label: 'Add Organization', path: '/organizations/add' },
    { label: 'Organization Dashboard', path: orgPath() },
    { label: 'Organization Usage', path: orgPath('/usage') },
    { label: 'Organization Team Members', path: orgPath('/users') },
    { label: 'Invite Org User', path: orgPath('/users/invite') },
  ],

  platformAdmin: [
    { label: 'Platform Admin', path: platformAdminPath() },
    { label: 'Platform Admin Summary', path: platformAdminPath('/summary') },
    { label: 'Platform Admin Live Services', path: platformAdminPath('/live-services') },
    { label: 'Platform Admin Trial Services', path: platformAdminPath('/trial-services') },
    { label: 'Platform Admin Reports', path: platformAdminPath('/reports') },
    { label: 'Platform Admin Complaints', path: platformAdminPath('/complaints') },
    { label: 'Platform Admin Clear Cache', path: platformAdminPath('/clear-cache') },
  ],

  platformAdminReports: [
    { label: 'Usage Report', path: platformAdminPath('/reports/usage-for-all-services') },
    { label: 'Volumes by Service', path: platformAdminPath('/reports/volumes-by-service') },
    { label: 'Daily Volumes', path: platformAdminPath('/reports/daily-volumes-report') },
  ],

  platformAdminService: [
    { label: 'Switch Service Live', path: servicePath('/service-settings/switch-live') },
    { label: 'Switch Count as Live', path: servicePath('/service-settings/switch-count-as-live') },
    { label: 'Set Rate Limit', path: servicePath('/service-settings/set-rate-limit') },
    { label: 'Set Message Limit', path: servicePath('/service-settings/set-message-limit') },
    { label: 'Set SMS Allowance', path: servicePath('/service-settings/set-free-sms-allowance') },
  ],

  documentation: [
    { label: 'Documentation', path: '/documentation' },
    { label: 'Create Messages', path: '/using-notify/how-to/create-and-send-messages' },
    { label: 'Edit Messages', path: '/using-notify/how-to/edit-and-format-messages' },
    { label: 'Send Files by Email', path: '/using-notify/how-to/send-files-by-email' },
  ],

  usingNotify: [
    { label: 'Get Started', path: '/using-notify/get-started' },
    { label: 'Trial Mode', path: '/using-notify/trial-mode' },
    { label: 'Pricing', path: '/using-notify/pricing' },
    { label: 'Delivery Status', path: '/using-notify/delivery-status' },
    { label: 'How To', path: '/using-notify/how-to' },
    { label: 'Best Practices', path: '/using-notify/best-practices' },
  ],

  bestPractices: [
    { label: 'Clear Goals', path: '/using-notify/best-practices/clear-goals' },
    { label: 'Rules and Regulations', path: '/using-notify/best-practices/rules-and-regulations' },
    { label: 'Establish Trust', path: '/using-notify/best-practices/establish-trust' },
    { label: 'Write for Action', path: '/using-notify/best-practices/write-for-action' },
    { label: 'Multiple Languages', path: '/using-notify/best-practices/multiple-languages' },
    { label: 'Benchmark Performance', path: '/using-notify/best-practices/benchmark-performance' },
  ],

  about: [
    { label: 'About', path: '/about' },
    { label: 'Why Text Messaging', path: '/about/why-text-messaging' },
    { label: 'Security', path: '/about/security' },
  ],
};

const allRoutes = [
  ...routes.public,
  ...routes.errors,
  ...routes.service,
  ...routes.serviceSettings,
  ...routes.templates,
  ...routes.api,
  ...routes.userProfile,
  ...routes.organizations,
  ...routes.platformAdmin,
  ...routes.platformAdminReports,
  ...routes.platformAdminService,
  ...routes.documentation,
  ...routes.usingNotify,
  ...routes.bestPractices,
  ...routes.about,
];

const createFullUrl = (base, path) => `${base}${path}`;

const constructUrls = (base, routes) =>
  routes.reduce((acc, { label, path }) => {
    acc[label] = createFullUrl(base, path);
    return acc;
  }, {});

module.exports = {
  baseUrl,
  urls: constructUrls(baseUrl, allRoutes),
  routes,
};
