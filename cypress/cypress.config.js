const { defineConfig } = require('cypress')
const getCompareSnapshotsPlugin = require('cypress-image-diff-js/plugin')
const os = require('os')
const { execSync } = require('child_process')

module.exports = defineConfig({
  retries: 2,
  e2e: {
    baseUrl: process.env.CYPRESS_baseUrl || 'http://website:8080',
    supportFile: 'cypress/support/e2e.js',
    specPattern: 'cypress/e2e/**/*.cy.js',
    video: false,
    screenshotOnRunFailure: true,
    screenshotsFolder: 'cypress/reports/screenshots',
    videosFolder: 'cypress/reports/videos',
    testIsolation: true,
    chromeWebSecurity: false,
    setupNodeEvents(on, config) {
      // Register the cypress-image-diff-js plugin
      getCompareSnapshotsPlugin(on, config)

      on('before:browser:launch', (browser, launchOptions) => {
        // Ensure screenshots capture everything on "macbook-16" viewport
        launchOptions.args.push('--window-size=1536,960')

        if (browser.family === 'chromium' && browser.name !== 'electron') {
          // Stabilize text/edge rendering for visual regression in Docker/Linux
          launchOptions.args.push(
            '--force-device-scale-factor=1',
            '--font-render-hinting=none',
            '--disable-lcd-text',
            '--disable-font-subpixel-positioning',
            // Align Skia/GPU paths across hosts (reduces AA fringe variance)
            '--disable-skia-runtime-opts',
            '--disable-gpu',
            '--disable-gpu-compositing',
            '--disable-composited-antialiasing',
            '--disable-canvas-aa',
            '--disable-2d-canvas-clip-aa'
          )
        }

        return launchOptions
      });

      // implement node event listeners here
      on('task', {
        log(message) {
          console.log(message)
          return null
        },
        table(message) {
          console.table(message)
          return null
        }
      });

      on('before:run', (details) => {
        const sh = (cmd) => {
          try {
            return execSync(cmd, { encoding: 'utf8' }).trim()
          } catch (e) {
            return `ERROR: ${e.message}`
          }
        }

        console.log('=== Visual env diagnostics ===')
        console.log(`Cypress: ${details.cypressVersion}`)
        console.log(
          `Browser: ${details.browser?.displayName} ${details.browser?.version}`
        )
        console.log(`Browser path: ${details.browser?.path || 'n/a'}`)
        console.log(`Node: ${process.version}`)
        console.log(`Platform: ${process.platform} ${process.arch}`)
        console.log(`os.arch/release: ${os.arch()} / ${os.release()}`)
        console.log(`uname -m: ${sh('uname -m')}`)
        console.log(`cwd: ${process.cwd()}`)
        console.log(
          `DOCKER_DEFAULT_PLATFORM: ${process.env.DOCKER_DEFAULT_PLATFORM || '(unset)'}`
        )
        console.log(
          `TZ/LANG: ${process.env.TZ || '(unset)'} / ${process.env.LANG || '(unset)'}`
        )
        console.log(
          `chromium: ${sh('chromium --version || chromium-browser --version')}`
        )
        console.log(
          `fc-list Public Sans: ${sh('fc-list : family | grep -i "public sans" | sort -u')}`
        )
        console.log(
          `fc-list Inter: ${sh('fc-list : family | grep -i "^inter" | sort -u')}`
        )
        console.log(
          `fc-list Schoolbook: ${sh('fc-list : family | grep -i schoolbook | sort -u')}`
        )
        console.log(
          `dpkg fonts: ${sh("dpkg -l 'fonts-*' 'chromium*' 2>/dev/null | awk '/^ii/{print $2, $3}'")}`
        )
        console.log(
          `cypressImageDiff env: ${JSON.stringify(
            config.env?.cypressImageDiff ||
              config.expose?.cypressImageDiff ||
              null
          )}`
        )
        console.log(
          `viewport: ${config.viewportWidth}x${config.viewportHeight}`
        )
        console.log('=== end diagnostics ===')
      })

      return config;
    },
  },
})
