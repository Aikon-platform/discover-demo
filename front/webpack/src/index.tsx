import { createRoot } from 'react-dom/client';
import ClusterApp from "./ClusterApp";

function initClusterViewer(element_id: string, result_data: any, base_media_url: string) {
    createRoot(document.getElementById(element_id)!).render(<ClusterApp result_data={result_data} />);
  }

export { initClusterViewer };