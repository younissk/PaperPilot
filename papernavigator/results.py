"""Results management for organized storage of query results.

This module provides ResultsManager for organizing all results from a query
into a dedicated directory structure.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


class ResultsManager:
    """Manages organized storage of query results.
    
    Creates a directory structure like:
    results/
    └── query_slug/
        ├── metadata.json
        ├── snowball.json
        ├── elo_ranked.json
        ├── clusters.json
        └── clusters.html
    """

    def __init__(self, base_dir: Path | str = "results"):
        """Initialize the results manager.
        
        Args:
            base_dir: Base directory for storing results (default: "results")
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _slugify(self, query: str) -> str:
        """Convert query to a filesystem-safe slug.
        
        Args:
            query: Research query string
            
        Returns:
            Slugified version safe for filesystem
        """
        # Convert to lowercase
        slug = query.lower()
        # Replace spaces and special chars with underscores
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '_', slug)
        # Remove leading/trailing underscores
        slug = slug.strip('_')
        # Limit length
        if len(slug) > 100:
            slug = slug[:100]
        return slug

    def _build_filename(self, base: str, params: dict[str, Any], extension: str = "json") -> str:
        """Build a parameterized filename from base name and parameters.
        
        Args:
            base: Base filename (e.g., "elo_ranked", "clusters")
            params: Dictionary of parameters to include in filename
            extension: File extension (default: "json")
            
        Returns:
            Parameterized filename (e.g., "elo_ranked_swiss_k32.json")
        """
        if not params:
            return f"{base}.{extension}"

        # Build parameter string
        parts = []
        for key, value in sorted(params.items()):
            if value is None:
                continue
            # Convert value to string, handle special cases
            if isinstance(value, float):
                # Remove decimal point for integers, keep 1 decimal for floats
                if value.is_integer():
                    val_str = str(int(value))
                else:
                    val_str = str(value).replace('.', 'd')  # e.g., 32.5 -> 32d5
            elif isinstance(value, bool):
                val_str = "1" if value else "0"
            else:
                val_str = str(value)

            # Shorten common parameter names
            key_map = {
                "pairing": "p",
                "k_factor": "k",
                "method": "m",
                "dim_reduction": "d",
                "n_clusters": "k",
                "direction": "dir",
                "limit": "l",
            }
            short_key = key_map.get(key, key)
            parts.append(f"{short_key}{val_str}")

        if parts:
            return f"{base}_{'_'.join(parts)}.{extension}"
        return f"{base}.{extension}"

    def get_query_dir(self, query: str) -> Path:
        """Get or create directory for a query.
        
        Args:
            query: Research query string
            
        Returns:
            Path to query-specific directory
        """
        slug = self._slugify(query)
        query_dir = self.base_dir / slug
        query_dir.mkdir(parents=True, exist_ok=True)
        return query_dir

    def save_metadata(
        self,
        query: str,
        metadata: dict[str, Any],
        overwrite: bool = False
    ) -> Path:
        """Save metadata for a query run.
        
        Args:
            query: Research query string
            metadata: Metadata dictionary (will be merged with existing)
            overwrite: If True, overwrite existing metadata
            
        Returns:
            Path to saved metadata file
        """
        query_dir = self.get_query_dir(query)
        metadata_file = query_dir / "metadata.json"

        if metadata_file.exists() and not overwrite:
            with open(metadata_file, encoding="utf-8") as f:
                existing = json.load(f)
            # Merge with existing
            existing.update(metadata)
            metadata = existing

        # Add/update timestamp
        metadata["last_updated"] = datetime.now().isoformat()
        if "created_at" not in metadata:
            metadata["created_at"] = datetime.now().isoformat()
        metadata["query"] = query

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return metadata_file

    def save_snowball(
        self,
        query: str,
        data: dict[str, Any],
        filename: str = "snowball.json"
    ) -> Path:
        """Save snowball search results.
        
        Args:
            query: Research query string
            data: Results data dictionary
            filename: Optional custom filename (default: "snowball.json")
            
        Returns:
            Path to saved file
        """
        query_dir = self.get_query_dir(query)
        output_file = query_dir / filename

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Update metadata
        self.save_metadata(query, {
            "snowball_file": filename,
            "snowball_count": data.get("total_accepted", len(data.get("papers", []))),
        })

        return output_file

    def save_elo_ranking(
        self,
        query: str,
        data: dict[str, Any],
        filename: str | None = None,
        pairing: str | None = None,
        k_factor: float | None = None,
    ) -> Path:
        """Save Elo ranking results.
        
        Args:
            query: Research query string
            data: Ranking data dictionary
            filename: Optional custom filename (if None, generates from parameters)
            pairing: Pairing strategy (swiss/random) for filename generation
            k_factor: K-factor for filename generation
            
        Returns:
            Path to saved file
        """
        query_dir = self.get_query_dir(query)

        # Generate filename from parameters if not provided
        if filename is None:
            params = {}
            if pairing:
                params["pairing"] = pairing
            if k_factor is not None:
                params["k_factor"] = k_factor
            filename = self._build_filename("elo_ranked", params, "json")

        output_file = query_dir / filename

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Update metadata
        self.save_metadata(query, {
            "elo_file": filename,
            "elo_matches": data.get("total_matches", 0),
            "elo_papers": data.get("total_papers", 0),
        })

        return output_file

    def save_clusters(
        self,
        query: str,
        json_data: dict[str, Any],
        html_content: str | None = None,
        json_filename: str | None = None,
        html_filename: str | None = None,
        method: str | None = None,
        dim_reduction: str | None = None,
        n_clusters: int | None = None,
    ) -> tuple[Path, Path | None]:
        """Save clustering results.
        
        Args:
            query: Research query string
            json_data: Cluster data dictionary
            html_content: Optional HTML visualization content
            json_filename: Optional custom JSON filename (if None, generates from parameters)
            html_filename: Optional custom HTML filename (if None, generates from parameters)
            method: Clustering method for filename generation
            dim_reduction: Dimension reduction method for filename generation
            n_clusters: Number of clusters for filename generation (kmeans only)
            
        Returns:
            Tuple of (json_path, html_path or None)
        """
        query_dir = self.get_query_dir(query)

        # Generate filenames from parameters if not provided
        if json_filename is None:
            params = {}
            if dim_reduction:
                params["dim_reduction"] = dim_reduction
            if method:
                params["method"] = method
            if n_clusters is not None:
                params["n_clusters"] = n_clusters
            json_filename = self._build_filename("clusters", params, "json")

        if html_filename is None and html_content:
            params = {}
            if dim_reduction:
                params["dim_reduction"] = dim_reduction
            if method:
                params["method"] = method
            if n_clusters is not None:
                params["n_clusters"] = n_clusters
            html_filename = self._build_filename("clusters", params, "html")

        json_path = query_dir / json_filename

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        html_path = None
        if html_content:
            html_path = query_dir / html_filename
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)

        # Update metadata
        self.save_metadata(query, {
            "clusters_json": json_filename,
            "clusters_html": html_filename if html_content else None,
            "n_clusters": json_data.get("n_clusters", 0),
            "clustering_method": json_data.get("method"),
            "dim_reduction": json_data.get("dim_reduction"),
        })

        return json_path, html_path

    def save_timeline(
        self,
        query: str,
        json_data: dict[str, Any],
        html_content: str | None = None,
        json_filename: str | None = None,
        html_filename: str | None = None,
    ) -> tuple[Path, Path | None]:
        """Save timeline results.
        
        Args:
            query: Research query string
            json_data: Timeline data dictionary
            html_content: Optional HTML visualization content
            json_filename: Optional custom JSON filename (default: "timeline.json")
            html_filename: Optional custom HTML filename (default: "timeline.html")
            
        Returns:
            Tuple of (json_path, html_path or None)
        """
        query_dir = self.get_query_dir(query)

        json_filename = json_filename or "timeline.json"
        html_filename = html_filename or "timeline.html"

        json_path = query_dir / json_filename

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        html_path = None
        if html_content:
            html_path = query_dir / html_filename
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)

        # Update metadata
        self.save_metadata(query, {
            "timeline_json": json_filename,
            "timeline_html": html_filename if html_content else None,
        })

        return json_path, html_path

    def save_graph(
        self,
        query: str,
        json_data: dict[str, Any],
        html_content: str | None = None,
        json_filename: str | None = None,
        html_filename: str | None = None,
        direction: str | None = None,
        limit: int | None = None,
    ) -> tuple[Path, Path | None]:
        """Save citation/reference graph results.
        
        Args:
            query: Research query string
            json_data: Graph data dictionary
            html_content: Optional HTML visualization content
            json_filename: Optional custom JSON filename (if None, generates from parameters)
            html_filename: Optional custom HTML filename (if None, generates from parameters)
            direction: Graph direction (both/citations/references) for filename generation
            limit: Limit per paper for filename generation
            
        Returns:
            Tuple of (json_path, html_path or None)
        """
        query_dir = self.get_query_dir(query)

        # Generate filenames from parameters if not provided
        if json_filename is None:
            params = {}
            if direction:
                params["direction"] = direction
            if limit is not None:
                params["limit"] = limit
            json_filename = self._build_filename("graph", params, "json")

        if html_filename is None and html_content:
            params = {}
            if direction:
                params["direction"] = direction
            if limit is not None:
                params["limit"] = limit
            html_filename = self._build_filename("graph", params, "html")

        json_path = query_dir / json_filename

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        html_path = None
        if html_content:
            html_path = query_dir / html_filename
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)

        # Update metadata
        self.save_metadata(query, {
            "graph_json": json_filename,
            "graph_html": html_filename if html_content else None,
        })

        return json_path, html_path

    def save_report(
        self,
        query: str,
        report_data: dict[str, Any],
        filename: str = "report.json",
        top_k: int | None = None,
    ) -> Path:
        """Save generated research report.
        
        Args:
            query: Research query string
            report_data: Report data dictionary
            filename: Optional custom filename (default: "report.json")
            top_k: Number of top papers used (for metadata)
            
        Returns:
            Path to saved report file
        """
        query_dir = self.get_query_dir(query)

        # Generate parameterized filename if top_k provided
        if top_k is not None and filename == "report.json":
            filename = self._build_filename("report", {"top_k": top_k}, "json")

        output_file = query_dir / filename

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        # Update metadata
        self.save_metadata(query, {
            "report_file": filename,
            "report_papers_used": report_data.get("total_papers_used", 0),
            "report_sections": len(report_data.get("current_research", [])),
            "report_generated_at": report_data.get("generated_at"),
        })

        return output_file

    def get_latest_elo(self, query: str) -> Path | None:
        """Get path to latest elo ranking results for a query.
        
        Args:
            query: Research query string
            
        Returns:
            Path to elo file, or None if not found
        """
        query_dir = self.get_query_dir(query)
        metadata_file = query_dir / "metadata.json"

        if metadata_file.exists():
            try:
                with open(metadata_file, encoding="utf-8") as f:
                    metadata = json.load(f)
                    elo_file = metadata.get("elo_file")
                    if elo_file:
                        elo_path = query_dir / elo_file
                        if elo_path.exists():
                            return elo_path
            except (json.JSONDecodeError, KeyError):
                pass

        # Fallback: look for any elo_ranked*.json file
        elo_files = list(query_dir.glob("elo_ranked*.json"))
        if elo_files:
            # Return the most recently modified one
            return max(elo_files, key=lambda p: p.stat().st_mtime)

        return None

    def list_queries(self) -> list[str]:
        """List all queries that have results.
        
        Returns:
            List of query strings (from metadata)
        """
        queries = []
        for query_dir in self.base_dir.iterdir():
            if query_dir.is_dir():
                metadata_file = query_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, encoding="utf-8") as f:
                            metadata = json.load(f)
                            queries.append(metadata.get("query", query_dir.name))
                    except (json.JSONDecodeError, KeyError):
                        # Fallback to directory name
                        queries.append(query_dir.name)
        return sorted(queries)

    def get_latest_snowball(self, query: str) -> Path | None:
        """Get path to latest snowball results for a query.
        
        Args:
            query: Research query string
            
        Returns:
            Path to snowball file, or None if not found
        """
        query_dir = self.get_query_dir(query)
        metadata_file = query_dir / "metadata.json"

        if metadata_file.exists():
            try:
                with open(metadata_file, encoding="utf-8") as f:
                    metadata = json.load(f)
                    snowball_file = metadata.get("snowball_file", "snowball.json")
                    snowball_path = query_dir / snowball_file
                    if snowball_path.exists():
                        return snowball_path
            except (json.JSONDecodeError, KeyError):
                pass

        # Fallback: check for default filename
        default_path = query_dir / "snowball.json"
        if default_path.exists():
            return default_path

        return None

    def get_metadata(self, query: str) -> dict[str, Any] | None:
        """Get metadata for a query.
        
        Args:
            query: Research query string
            
        Returns:
            Metadata dictionary, or None if not found
        """
        query_dir = self.get_query_dir(query)
        metadata_file = query_dir / "metadata.json"

        if metadata_file.exists():
            try:
                with open(metadata_file, encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return None

        return None
