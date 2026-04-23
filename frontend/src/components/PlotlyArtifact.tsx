import createPlotlyComponent from "react-plotly.js/factory";
import Plotly from "plotly.js-basic-dist-min";

const Plot = createPlotlyComponent(Plotly);

type PlotlyArtifactProps = {
  plotlyJson: Record<string, unknown>;
};

export default function PlotlyArtifact({ plotlyJson }: PlotlyArtifactProps) {
  return (
    <Plot
      data={(plotlyJson.data as object[]) ?? []}
      layout={(plotlyJson.layout as object) ?? {}}
      config={{ responsive: true, displaylogo: false }}
      style={{ width: "100%", height: "100%" }}
      useResizeHandler
    />
  );
}
