# README assets

Drop the following files in this folder to make the main README render with screenshots and a demo GIF:

| Filename | What it should show | Suggested size |
|---|---|---|
| `logo.svg` | Ariya mark (already included) | 96 × 96 |
| `screenshot-dark.png` | Dark-mode chat view with an uploaded dataset and a generated Plotly chart | 1600 × 1000 |
| `screenshot-light.png` | Light-mode view with the dataset profile table visible | 1600 × 1000 |
| `demo.gif` *(optional)* | 10–20 second loop: upload CSV → ask question → chart appears | ≤ 8 MB |

## How to capture good screenshots

1. Run the app locally (`npm run dev` + `uvicorn app.main:app --reload`).
2. Upload a public, non-sensitive dataset (Kaggle Titanic, NYC taxi samples, etc.).
3. Resize the browser to **1600 × 1000** for consistent framing.
4. Use the OS screenshotter (Win + Shift + S on Windows, Cmd + Shift + 4 on macOS).
5. For the GIF, tools like [ScreenToGif](https://www.screentogif.com/) (Windows) or [Kap](https://getkap.co/) (macOS) work well.

## Tip for recruiter appeal

The first screenshot is the one people scroll past on GitHub — make it the **result** of an analysis (a beautiful chart), not the empty upload state.
