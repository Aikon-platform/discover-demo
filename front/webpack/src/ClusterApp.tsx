import { useEffect } from "react";
import { ClusterElement, ClusterProps, ImageProps } from "./ClusterElement";

interface AppProps {
  result_data: {
    clusters: {
      id: number;
      proto_url: string;
      mask_url: string;
      images: {
        cluster_id: number;
        distance: number;
        path: string;
        raw_url: string;
        tsf_url: string;
      }[];
    }[];
    base_url: string;
  };
}

export default function ClusterApp({ result_data }: AppProps) {
  console.log(result_data);
  const clusters = result_data.clusters.map((cluster) => {
    const images = cluster.images.map((image) => {
      return {
        origpath: image.path,
        raw_url: result_data.base_url + image.raw_url,
        tsf_url: result_data.base_url + image.tsf_url,
        distance: image.distance,
      };
    });
    return {
      id: cluster.id,
      images: images,
      proto_url: result_data.base_url + cluster.proto_url,
      mask_url: cluster.mask_url ? result_data.base_url + cluster.mask_url : undefined,
    };
  }).sort((a, b) => b.images.length - a.images.length);

  return (
    <div>
      <h1>Cluster Viewer</h1>
      <div className="cluster-list">
      {clusters.map((cluster) => (
        <ClusterElement key={cluster.id} {...cluster} />
      ))}
      </div>
    </div>
  );
}
