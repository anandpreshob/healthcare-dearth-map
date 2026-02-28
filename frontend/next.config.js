/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",

  // If deploying to github.com/username/healthcare-dearth-map,
  // set basePath to "/healthcare-dearth-map".
  // For a custom domain or github.io root, leave it empty.
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || "",

  // Static assets also need the prefix
  assetPrefix: process.env.NEXT_PUBLIC_BASE_PATH || "",

  // Disable image optimization (not available in static export)
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;
