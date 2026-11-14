# Third-party notices

## Euron Open Conversation

The development candidate in `foundation/euron` is adapted from [Euron Open Conversation](https://github.com/euron-sde-team/euron-open-real-time-ai-conversation-system) at commit `216a8fc52a055587f436f2446f1a80b6868bd14a`, copyright 2026 ENGAGESPHERE TECHNOLOGY PRIVATE LIMITED and the Euron Open Conversation contributors. The upstream MIT license and copyright notice are retained in [foundation/euron/LICENSE](foundation/euron/LICENSE). The foundation README lists local modifications. Marketing assets and unrelated documentation were excluded.

## MediaPipe model

The upstream copy includes `foundation/euron/apps/web/public/mediapipe/blaze_face_short_range.tflite` (SHA-256 `b4578f35940bf5a1a655214a1cce5cab13eba73c1297cd78e1a04c2380b0152f`), used only for the optional browser face-presence feature. Upstream identifies this model as Apache-2.0; the [MediaPipe project](https://github.com/google-ai-edge/mediapipe) provides its [model card](https://storage.googleapis.com/mediapipe-assets/MediaPipe%20BlazeFace%20Model%20Card%20(Short%20Range).pdf). The [Apache-2.0 license text](foundation/euron/third-party/APACHE-2.0.txt) is included. Reconfirm exact weight provenance and redistribution obligations before a commercial release.

## Installed dependencies

The pnpm lockfile identifies npm dependencies; each retains its own license. An initial local metadata review found permissive licenses, OFL-1.1 fonts, MPL-2.0 test dependencies, and LGPL-3.0-or-later `@img/sharp-libvips` binaries. Four packages without a `license` field in the local metadata (`streamsearch`, `busboy`, `rechoir`, `png-js`) contain MIT license text. This is a preliminary inventory, not a complete transitive license or distribution review. Produce a reproducible SBOM and satisfy applicable license/notice obligations before shipping.
