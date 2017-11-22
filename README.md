# Sublime Plugin Import Cost

Sublime Text 3 plugin that shows the [import costs](https://github.com/wix/import-cost/) of imported JS modules.

![Example GIF](./example.gif)

**NOTE:** This is more an experiment, with the core written by drunk Julian after the Oktoberfest 😉 I am by no means a Python developer, so usage of the plugin is at your own risk of running into performance issues. PRs with improvements are very welcome 😅

## Todos

 - [x] ~~Add basic menus and settings~~
 - [x] ~~Add "show gzip" option~~
 - [ ] Make plugin available through plugin manager
 - [x] Make plugin smarter to always find correct node_modules folder, no matter what folder is currently open in sublime
 - [ ] Add caching on python level (import-cost has caching itself, but we still have the expensive node bridge thing going on, which is very avoidable)
 - [ ] Windows support
