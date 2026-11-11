/** @type {import('@docusaurus/types').Config} */
const config = {
  title: "Product docs",
  tagline: "Official documentation exported from AI-DLC",
  url: "https://example.invalid",
  baseUrl: "/",
  organizationName: "product",
  projectName: "docs-site",
  onBrokenLinks: "throw",
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: "warn",
    },
  },
  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },
  presets: [
    [
      "classic",
      {
        docs: {
          sidebarPath: require.resolve("./sidebars.js"),
          routeBasePath: "/",
        },
        blog: false,
        theme: {
          customCss: require.resolve("./src/css/custom.css"),
        },
      },
    ],
  ],
};

module.exports = config;
