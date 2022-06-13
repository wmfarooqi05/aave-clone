/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['encrypted-tbn0.gstatic.com', 'cdn.sanity.io'],
  },
}


module.exports = {
  images: {
    domains: ['s2.coinmarketcap.com', 's3.coinmarketcap.com', 'cdn.sanity.io', 'encrypted-tbn0.gstatic.com']
  },
  env: {
    MORALIS_SERVER_URL: process.env.MORALIS_SERVER_URL,
    MORALIS_API_KEY: process.env.MORALIS_API_KEY,
    NEXT_BACKEND_CMC_API_KEY: process.env.NEXT_BACKEND_CMC_API_KEY,
  },
  nextConfig
}
