const baseUrl = process.env.BACKSTOP_BASE_URL || 'http://localhost:6012';

// List of routes organized by section
const routes = {
  // Main pages
  main: [
    { label: 'Homepage', path: '/' },
    { label: 'Add Service', path: '/add-service' },
    { label: 'Support', path: '/support' },
    { label: 'Notify.gov Service Ending', path: '/notify-service-ending' },
    { label: 'Notify.gov Sign In', path: '/sign-in' },
    { label: 'Accessibility Statement', path: '/accessibility-statement' },
    { label: 'Privacy', path: '/privacy' },
    { label: 'Email Not Received', path: '/email-not-received' },
    { label: 'Text Not Received', path: '/text-not-received' },
    { label: 'Performance', path: '/performance' },
    // Registration pages with radio buttons
    // Note: /register returns 404, registration is handled through login.gov
    // { label: 'Register', path: '/register' },
    // { label: 'Register From Invite', path: '/register/from-invite/example-token' },
  ],

  authenticated: [
    {
      label: 'SMS Template Preview',
      path: '/services/da14b8fa-6a9e-4320-8484-9cd6e900c333/send/31588995-646b-40ae-bed1-617612d9245e/one-off/step-0',
    },
    // Pages with USWDS buttons that need testing
    {
      label: 'API Keys',
      path: '/services/da14b8fa-6a9e-4320-8484-9cd6e900c333/api/keys',
    },
    {
      label: 'API Keys Create',
      path: '/services/da14b8fa-6a9e-4320-8484-9cd6e900c333/api/keys/create',
    },
    {
      label: 'Change User Auth',
      path: '/users/6af522d0-2915-4e52-83a3-3690455a5fe6/change_auth',
    },
    {
      label: 'User Profile Timezone',
      path: '/user-profile/preferred_timezone',
    },
    {
      label: 'Service Settings',
      path: '/services/da14b8fa-6a9e-4320-8484-9cd6e900c333/service-settings',
    },
    {
      label: 'Service Send Files By Email',
      path: '/services/da14b8fa-6a9e-4320-8484-9cd6e900c333/service-settings/send-files-by-email',
    },
    {
      label: 'Service SMS Prefix',
      path: '/services/da14b8fa-6a9e-4320-8484-9cd6e900c333/service-settings/sms-prefix',
    },
    {
      label: 'Send One Off Step 2',
      path: '/services/da14b8fa-6a9e-4320-8484-9cd6e900c333/send/31588995-646b-40ae-bed1-617612d9245e/one-off/step-2',
    },
    {
      label: 'Choose Template',
      path: '/services/da14b8fa-6a9e-4320-8484-9cd6e900c333/templates',
    },
    {
      label: 'Team Members',
      path: '/services/da14b8fa-6a9e-4320-8484-9cd6e900c333/users',
    },
    {
      label: 'All Activity',
      path: '/activity/services/da14b8fa-6a9e-4320-8484-9cd6e900c333',
    },
    {
      label: 'Invite User',
      path: '/services/da14b8fa-6a9e-4320-8484-9cd6e900c333/users/invite',
    },
    {
      label: 'Platform Admin Live Services',
      path: '/platform-admin/live-services',
    },
    {
      label: 'Add Organization',
      path: '/organizations/add',
    },
    {
      label: 'Uploads',
      path: '/services/da14b8fa-6a9e-4320-8484-9cd6e900c333/uploads',
    },
    {
      label: 'API Guest List',
      path: '/services/da14b8fa-6a9e-4320-8484-9cd6e900c333/api/guest-list',
    },
    // User profile and auth pages with radio buttons
    // Note: /set-up-your-profile requires special auth flow from login.gov
    // {
    //   label: 'Set Up Your Profile',
    //   path: '/set-up-your-profile',
    // },
    {
      label: 'Platform Admin User Auth Type',
      path: '/users/6af522d0-2915-4e52-83a3-3690455a5fe6/change_auth',
    },
    // Service settings pages with radio buttons
    {
      label: 'Data Retention Add',
      path: '/services/da14b8fa-6a9e-4320-8484-9cd6e900c333/data-retention/add',
    },
    {
      label: 'Link Service to Organization',
      path: '/services/da14b8fa-6a9e-4320-8484-9cd6e900c333/service-settings/link-service-to-organization',
    },
    // Template sender pages with radio buttons
    {
      label: 'Set Template Sender',
      path: '/services/da14b8fa-6a9e-4320-8484-9cd6e900c333/send/31588995-646b-40ae-bed1-617612d9245e/set-sender',
    },
    {
      label: 'Set Template Letter Sender',
      path: '/services/da14b8fa-6a9e-4320-8484-9cd6e900c333/templates/31588995-646b-40ae-bed1-617612d9245e/set-template-sender',
    },
  ],

  // Using Notify section
  usingNotify: [
    { label: 'Get Started', path: '/using-notify/get-started' },
    { label: 'Trial Mode', path: '/using-notify/trial-mode' },
    { label: 'Pricing', path: '/using-notify/pricing' },
    { label: 'Delivery Status', path: '/using-notify/delivery-status' },
    { label: 'How To', path: '/using-notify/how-to' },
    { label: 'Best Practices', path: '/using-notify/best-practices' },
  ],

  // Best Practices subsection
  bestPractices: [
    { label: 'Clear Goals', path: '/using-notify/best-practices/clear-goals' },
    {
      label: 'Rules And Regulations',
      path: '/using-notify/best-practices/rules-and-regulations',
    },
    {
      label: 'Establish Trust',
      path: '/using-notify/best-practices/establish-trust',
    },
    {
      label: 'Write For Action',
      path: '/using-notify/best-practices/write-for-action',
    },
    {
      label: 'Multiple Languages',
      path: '/using-notify/best-practices/multiple-languages',
    },
    {
      label: 'Benchmark Performance',
      path: '/using-notify/best-practices/benchmark-performance',
    },
  ],

  // About section
  about: [
    { label: 'About', path: '/about' },
    { label: 'Why Text Messaging', path: '/about/why-text-messaging' },
    { label: 'Security', path: '/about/security' },
  ],
};

// Flatten all routes into a single array
const sublinks = [
  ...routes.main,
  ...routes.usingNotify,
  ...routes.bestPractices,
  ...routes.about,
  ...routes.authenticated,
  // Add more sections here as needed
];

const createFullUrl = (base, path) => `${base}${path}`;

// Build url using base and path
const constructUrls = (base, sublinks) =>
  sublinks.reduce((acc, { label, path }) => {
    return { ...acc, [label]: createFullUrl(base, path) };
  }, {});

module.exports = {
  baseUrl,
  urls: constructUrls(baseUrl, sublinks),
};
