# AndBible store screenshots

Store (Google Play, App Store) and website screenshots of AndBible, and the inputs that produce them. Included in
the main repository as the submodule `store-screenshots/` with `update = none`: normal clones and CI do not fetch it
(`git submodule update --init --checkout store-screenshots` does). The pipeline code lives in the main repository
under `scripts/store-shots/` (issue #4021; spec `docs/superpowers/specs/2026-11-07-6-0-store-screenshots-design.md`
in the private process submodule).

## Layout

| Path | What |
|------|------|
| `shots.yaml` | The shot list: id, demo workspace, scripted action, light/dark, targets, caption key |
| `captions/<lang>.yaml` | Caption per shot (English source; other languages are translated in phase 2) |
| `demo-content/<lang>/content.yaml` | Demo labels, bookmarks with notes, a StudyPad and one workspace per scene |
| `demo-content/modules.yaml` | Sword modules per language (all freely installable from the app's repositories) |
| `demo-content/modules-table.md` | Proposed Bible per language (48 Play + 12 App Store languages), for review |
| `style/` | Background, device frames (`make_style.py` regenerates them), `fonts.yaml` + `fetch-fonts.sh` |
| `review/<lang>/` | A language's framed set and contact sheets waiting for review |
| `android/<play locale>/{phone,seven-inch,ten-inch}/NN.png` | Approved Play images |
| `ios/<App Store locale>/{iphone-6.9,iphone-6.5,ipad-13}/NN.png` | Approved App Store images |
| `website/{phone,desktop,mac}/NN.webp` | Approved website images (English) |

Font binaries are not committed: `style/fetch-fonts.sh` copies the Noto fonts (Debian packages `fonts-noto-core`,
`fonts-noto-cjk`) into the ignored `style/fonts/`; `scripts/store-shots/run.sh` runs it when they are missing.

## Targets

| Target | Final size | Captured on |
|--------|-----------|-------------|
| `play-phone` | 1080x1920 | emulator AVD `screenshot_phone` (Pixel 6 Pro, 1440x3120) |
| `play-seven` | 1920x1080 | AVD `screenshot_tablet7` (Nexus 7 2013, landscape 1920x1200) |
| `play-ten` | 2560x1440 | AVD `tablet_api36` (Pixel Tablet, landscape 2560x1600) |
| `ios-iphone-69` / `ios-iphone-65` | 1320x2868 / 1284x2778 | iPhone 16 Pro Max simulator (one capture, two framings) |
| `ios-ipad-13` | 2064x2752 | iPad Pro 13-inch (M4) simulator |
| `web-phone` | 1080x1920 | the `play-phone` raws |
| `web-desktop` | 1920x1200 | Linux desktop app (CEF), 1600x1000 window on Xvfb |
| `web-mac` | 1920x1200 | the iPad app as a Mac app: not scriptable on the build Mac (see below) |

All images are RGB without alpha (Play and the App Store reject alpha).

## Regenerate one language or one platform

Prerequisites: a JailBee container of the main repository (or any Linux with `uv`, Android SDK + emulator, JDK 17),
the submodule checked out, network access to the module repositories. Work files go to `.local/store-shots/`
(`STORE_SHOTS_WORK` overrides); nothing in there is committed.

```bash
# Demo backup + modules for a language (also done by every capture script)
scripts/store-shots/prepare-lang.sh en

# Android (one emulator at a time; never while the Windows VM runs)
./gradlew assembleStandardGithubDebug
scripts/store-shots/android-capture.sh --target play-phone --lang en
scripts/store-shots/android-capture.sh --target play-seven --lang en
scripts/store-shots/android-capture.sh --target play-ten --lang en
scripts/andbible-emu.sh kill

# iOS on the shared remote Mac (ios-mac skill: one Mac session at a time; the script ends with mac-remote cleanup)
scripts/store-shots/ios-capture.sh --device iphone --lang en
scripts/store-shots/ios-capture.sh --device ipad --lang en

# Linux desktop (website)
./gradlew :desktopApp:createDistributable
scripts/store-shots/desktop-capture.sh --lang en

# Frame, check, review, promote
scripts/store-shots/run.sh frame --lang en --platform android   # also ios, web
scripts/store-shots/run.sh status --lang en
scripts/store-shots/run.sh promote --lang en --review           # -> review/en/
scripts/store-shots/run.sh contact --lang en                    # -> review/en/contact-*.png
scripts/store-shots/run.sh promote --lang en                    # after approval: store folders
```

`--shots id,id` on the capture scripts reruns single shots; the run state (`.local/store-shots/<lang>/state.json`)
keeps the others, and `promote` refuses a language with any missing shot, so an interrupted run never ships half a
set.

## How a shot is made

The demo content (`content.yaml`) is turned into an ordinary AndBible database backup by the JVM generator
(`./gradlew :sharedLogic:generateDemoBackup`, used by `prepare-lang.sh`). Its database files are placed where the
app keeps them (Android `databases/` via `run-as`, the simulator's app container, the desktop profile), the same files
the app's restore writes, and the modules go into the app's module folder. Every workspace is one scene; the drivers
switch workspaces through the real Workspaces sheet and perform one scripted action (bookmark popup, note view, label
assignment, book chooser, search). Bookmark actions name a bookmark id; the verse to tap and the note text come from
`content.yaml`, so the recipes do not depend on the Bible text's language. Status bars are fixed at 9:41 with full
battery and signal (SystemUI demo mode, `simctl status_bar`). Dark shots use the system dark appearance.

## Play upload

`scripts/store-shots/fastlane-images.sh` copies `android/<locale>/...` into
`fastlane/metadata/android/<locale>/images/{phone,sevenInch,tenInch}Screenshots/` before `supply`; `--check` lists
per-locale counts and fails on a partial locale. The text metadata in `fastlane/metadata/android/` is not touched.

## Not automated

- `web-mac`: the build Mac cannot launch the unsigned "Designed for iPad" build as a Mac app (LaunchServices -10668),
  so the 1-2 Mac window images are taken by the maintainer on a Mac with the TestFlight build (`screencapture -l -o`
  of the app window, cropped to the content and scaled to exactly 1600x1000 px), saved as `<shot id>.png` and imported with
  `scripts/store-shots/run.sh record --lang en --target web-mac --dir <folder>` (then add `web-mac` back to the
  shots' targets in `shots.yaml`).
- Windows desktop: the Linux desktop images serve the website's desktop slot; a Windows run would use the same flow
  in the `windows-vm` skill's VM (needs the orchestrator's VM token).
