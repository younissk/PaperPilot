"""Interactive CLI menu for PaperPilot.

Provides an interactive menu-driven interface for running searches,
viewing results, ranking, and clustering papers.
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.panel import Panel
from rich.text import Text
from rich import box

from paperpilot.cli.console import print_header, print_error, print_success
from paperpilot.core.results import ResultsManager


console = Console()


@dataclass
class SearchConfig:
    """Configuration for a search operation."""
    query: str
    num_results: int = 5
    max_iterations: int = 5
    max_accepted: int = 200
    top_n: int = 50


@dataclass
class ClusteringConfig:
    """Configuration for clustering operation."""
    method: str = "hdbscan"
    n_clusters: Optional[int] = None
    dim_method: str = "umap"
    eps: Optional[float] = None
    min_samples: Optional[int] = None


def show_main_menu() -> str:
    """Display main menu and get user choice.
    
    Returns:
        User's menu choice
    """
    console.print()
    print_header("PaperPilot", "bold blue")
    
    menu_text = Text()
    menu_text.append("1. ", style="bold cyan")
    menu_text.append("Search for papers\n", style="white")
    menu_text.append("2. ", style="bold cyan")
    menu_text.append("View existing results\n", style="white")
    menu_text.append("3. ", style="bold cyan")
    menu_text.append("Rank papers (Elo)\n", style="white")
    menu_text.append("4. ", style="bold cyan")
    menu_text.append("Cluster papers\n", style="white")
    menu_text.append("5. ", style="bold cyan")
    menu_text.append("Create timeline\n", style="white")
    menu_text.append("6. ", style="bold cyan")
    menu_text.append("Build citation graph\n", style="white")
    menu_text.append("7. ", style="bold cyan")
    menu_text.append("Generate report\n", style="white")
    menu_text.append("8. ", style="bold cyan")
    menu_text.append("Run everything\n", style="white")
    menu_text.append("9. ", style="bold cyan")
    menu_text.append("Exit\n", style="white")
    
    panel = Panel(
        menu_text,
        title="[bold]Main Menu[/bold]",
        border_style="blue",
        box=box.ROUNDED,
    )
    console.print(panel)
    console.print()
    
    choice = Prompt.ask(
        "[bold cyan]What would you like to do?[/bold cyan]",
        choices=["1", "2", "3", "4", "5", "6", "7", "8", "9"],
        default="1",
    )
    
    return choice


def get_search_config() -> SearchConfig:
    """Get search configuration from user.
    
    Returns:
        SearchConfig with user's choices
    """
    console.print()
    print_header("Search Configuration", "bold cyan")
    
    query = Prompt.ask("[bold]Enter your research query[/bold]")
    
    num_results = IntPrompt.ask(
        "[bold]Number of results per query variant[/bold]",
        default=5,
        show_default=True,
    )
    
    max_iterations = IntPrompt.ask(
        "[bold]Maximum snowball iterations[/bold]",
        default=5,
        show_default=True,
    )
    
    max_accepted = IntPrompt.ask(
        "[bold]Maximum papers to accept[/bold]",
        default=200,
        show_default=True,
    )
    
    top_n = IntPrompt.ask(
        "[bold]Top N candidates to judge per iteration[/bold]",
        default=50,
        show_default=True,
    )
    
    return SearchConfig(
        query=query,
        num_results=num_results,
        max_iterations=max_iterations,
        max_accepted=max_accepted,
        top_n=top_n,
    )


def select_results_file(results_manager: ResultsManager) -> Optional[Path]:
    """Let user select a results file.
    
    Args:
        results_manager: ResultsManager instance
        
    Returns:
        Path to selected file, or None if cancelled
    """
    console.print()
    queries = results_manager.list_queries()
    
    if not queries:
        print_error("No existing results found. Run a search first.")
        return None
    
    print_header("Select Query Results", "bold cyan")
    
    # Show list of queries
    for i, query in enumerate(queries, 1):
        console.print(f"  [cyan]{i}.[/cyan] {query}")
    
    console.print()
    choice = IntPrompt.ask(
        "[bold]Select a query[/bold]",
        default=1,
    )
    
    if 1 <= choice <= len(queries):
        selected_query = queries[choice - 1]
        snowball_path = results_manager.get_latest_snowball(selected_query)
        if snowball_path:
            return snowball_path
        else:
            print_error(f"No snowball results found for: {selected_query}")
            return None
    else:
        print_error("Invalid selection")
        return None


def get_ranking_config() -> dict:
    """Get Elo ranking configuration from user.
    
    Returns:
        Dictionary with ranking configuration
    """
    console.print()
    print_header("Elo Ranking Configuration", "bold cyan")
    
    n_matches = IntPrompt.ask(
        "[bold]Number of matches[/bold] (0 for auto)",
        default=0,
        show_default=True,
    )
    n_matches = None if n_matches == 0 else n_matches
    
    k_factor = float(IntPrompt.ask(
        "[bold]K-factor[/bold]",
        default=32,
        show_default=True,
    ))
    
    pairing = Prompt.ask(
        "[bold]Pairing strategy[/bold]",
        choices=["swiss", "random"],
        default="swiss",
        show_default=True,
    )
    
    early_stop = Confirm.ask(
        "[bold]Enable early stopping[/bold]",
        default=True,
    )
    
    concurrency = IntPrompt.ask(
        "[bold]Max concurrent API calls[/bold]",
        default=5,
        show_default=True,
    )
    
    tournament = Confirm.ask(
        "[bold]Use tournament mode[/bold]",
        default=False,
    )
    
    return {
        "n_matches": n_matches,
        "k_factor": k_factor,
        "pairing": pairing,
        "early_stop": early_stop,
        "concurrency": concurrency,
        "tournament": tournament,
    }


def get_clustering_config() -> ClusteringConfig:
    """Get clustering configuration from user.
    
    Returns:
        ClusteringConfig with user's choices
    """
    console.print()
    print_header("Clustering Configuration", "bold cyan")
    
    method = Prompt.ask(
        "[bold]Clustering method[/bold]",
        choices=["hdbscan", "dbscan", "kmeans"],
        default="hdbscan",
        show_default=True,
    )
    
    dim_method = Prompt.ask(
        "[bold]Dimension reduction method[/bold]",
        choices=["umap", "tsne", "pca"],
        default="umap",
        show_default=True,
    )
    
    n_clusters = None
    if method == "kmeans":
        n_clusters = IntPrompt.ask(
            "[bold]Number of clusters[/bold]",
            default=5,
            show_default=True,
        )
    
    eps = None
    min_samples = None
    if method in ["dbscan", "hdbscan"]:
        eps_input = Prompt.ask(
            "[bold]Eps parameter[/bold] (leave empty for auto)",
            default="",
        )
        if eps_input:
            eps = float(eps_input)
        
        min_samples_input = Prompt.ask(
            "[bold]Min samples[/bold] (leave empty for default)",
            default="",
        )
        if min_samples_input:
            min_samples = int(min_samples_input)
    
    return ClusteringConfig(
        method=method,
        n_clusters=n_clusters,
        dim_method=dim_method,
        eps=eps,
        min_samples=min_samples,
    )


def get_report_config() -> dict:
    """Get report generation configuration from user.
    
    Returns:
        Dictionary with report configuration
    """
    console.print()
    print_header("Report Generation Configuration", "bold cyan")
    
    top_k = IntPrompt.ask(
        "[bold]Number of top papers to use[/bold]",
        default=30,
        show_default=True,
    )
    
    use_elo = Confirm.ask(
        "[bold]Use Elo ranking if available[/bold]",
        default=True,
    )
    
    return {
        "top_k": top_k,
        "use_elo": use_elo,
    }


def get_graph_config() -> dict:
    """Get graph building configuration from user.
    
    Returns:
        Dictionary with graph configuration
    """
    console.print()
    print_header("Graph Building Configuration", "bold cyan")
    
    direction = Prompt.ask(
        "[bold]Graph direction[/bold]",
        choices=["both", "citations", "references"],
        default="both",
        show_default=True,
    )
    
    limit = IntPrompt.ask(
        "[bold]Maximum refs/cites per paper[/bold]",
        default=100,
        show_default=True,
    )
    
    return {
        "direction": direction,
        "limit": limit,
    }


def run_interactive() -> None:
    """Run the interactive CLI menu loop."""
    results_manager = ResultsManager()
    
    while True:
        choice = show_main_menu()
        
        if choice == "1":
            # Search for papers
            try:
                config = get_search_config()
                console.print()
                print_success(f"Starting search for: {config.query}")
                console.print()
                
                # Import here to avoid circular imports
                from paperpilot.cli.app import run_search_with_display
                import asyncio
                
                asyncio.run(
                    run_search_with_display(
                        query=config.query,
                        num_results=config.num_results,
                        output_file="",  # Will use ResultsManager
                        max_iterations=config.max_iterations,
                        max_accepted=config.max_accepted,
                        top_n=config.top_n,
                    )
                )
            except KeyboardInterrupt:
                console.print()
                print_error("Search cancelled by user")
            except Exception as e:
                print_error(f"Search failed: {e}")
        
        elif choice == "2":
            # View existing results
            file_path = select_results_file(results_manager)
            if file_path:
                try:
                    from paperpilot.cli.app import results
                    # Call results command with selected file
                    results(str(file_path))
                except Exception as e:
                    print_error(f"Failed to display results: {e}")
        
        elif choice == "3":
            # Rank papers
            file_path = select_results_file(results_manager)
            if file_path:
                try:
                    config = get_ranking_config()
                    console.print()
                    print_success(f"Starting Elo ranking for: {file_path}")
                    console.print()
                    
                    from paperpilot.cli.app import run_elo_ranking
                    import asyncio
                    import json
                    
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    asyncio.run(
                        run_elo_ranking(
                            papers=data.get("papers", []),
                            query=data.get("query", "Unknown"),
                            n_matches=config["n_matches"],
                            k_factor=config["k_factor"],
                            pairing=config["pairing"],
                            early_stop=config["early_stop"],
                            concurrency=config["concurrency"],
                            tournament=config["tournament"],
                            output_file="",  # Will use ResultsManager
                            interactive=True,
                        )
                    )
                except KeyboardInterrupt:
                    console.print()
                    print_error("Ranking cancelled by user")
                except Exception as e:
                    print_error(f"Ranking failed: {e}")
        
        elif choice == "4":
            # Cluster papers
            file_path = select_results_file(results_manager)
            if file_path:
                try:
                    config = get_clustering_config()
                    console.print()
                    print_success(f"Starting clustering for: {file_path}")
                    console.print()
                    
                    from paperpilot.cli.app import run_clustering
                    import json
                    
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    run_clustering(
                        papers=data.get("papers", []),
                        query=data.get("query", "Unknown"),
                        cluster_method=config.method,
                        dim_method=config.dim_method,
                        n_clusters=config.n_clusters,
                        eps=config.eps,
                        min_samples=config.min_samples,
                        output_file="",  # Will use ResultsManager
                        html_file="",  # Will use ResultsManager
                    )
                except KeyboardInterrupt:
                    console.print()
                    print_error("Clustering cancelled by user")
                except Exception as e:
                    print_error(f"Clustering failed: {e}")
        
        elif choice == "5":
            # Create timeline
            file_path = select_results_file(results_manager)
            if file_path:
                try:
                    console.print()
                    print_success(f"Creating timeline for: {file_path}")
                    console.print()
                    
                    from paperpilot.cli.app import timeline
                    timeline(str(file_path))
                except KeyboardInterrupt:
                    console.print()
                    print_error("Timeline creation cancelled by user")
                except Exception as e:
                    print_error(f"Timeline creation failed: {e}")
        
        elif choice == "6":
            # Build citation graph
            file_path = select_results_file(results_manager)
            if file_path:
                try:
                    config = get_graph_config()
                    console.print()
                    print_success(f"Building graph for: {file_path}")
                    console.print()
                    
                    from paperpilot.cli.app import graph
                    graph(
                        str(file_path),
                        direction=config["direction"],
                        limit=config["limit"],
                    )
                except KeyboardInterrupt:
                    console.print()
                    print_error("Graph building cancelled by user")
                except Exception as e:
                    print_error(f"Graph building failed: {e}")
        
        elif choice == "7":
            # Generate report
            file_path = select_results_file(results_manager)
            if file_path:
                try:
                    config = get_report_config()
                    console.print()
                    print_success(f"Generating report for: {file_path}")
                    console.print()
                    
                    import asyncio
                    from paperpilot.core.report.generator import generate_report, report_to_dict
                    import json
                    
                    # Determine elo file if requested
                    elo_path = None
                    if config["use_elo"]:
                        parent_dir = file_path.parent
                        elo_candidates = list(parent_dir.glob("elo_ranked*.json"))
                        if elo_candidates:
                            elo_path = max(elo_candidates, key=lambda p: p.stat().st_mtime)
                            console.print(f"[dim]Using elo file: {elo_path.name}[/dim]")
                    
                    # Load query from file
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    query = data.get("query", "Unknown")
                    
                    # Generate report
                    report_obj = asyncio.run(
                        generate_report(
                            snowball_file=file_path,
                            elo_file=elo_path,
                            top_k=config["top_k"],
                        )
                    )
                    
                    # Save report
                    report_data = report_to_dict(report_obj)
                    output_path = results_manager.save_report(
                        query=query,
                        report_data=report_data,
                        top_k=config["top_k"],
                    )
                    
                    console.print()
                    print_success(f"Report saved to: {output_path}")
                    console.print(f"[bold]Sections:[/bold] {len(report_obj.current_research)}")
                    console.print(f"[bold]Open problems:[/bold] {len(report_obj.open_problems)}")
                    
                except KeyboardInterrupt:
                    console.print()
                    print_error("Report generation cancelled by user")
                except Exception as e:
                    print_error(f"Report generation failed: {e}")
        
        elif choice == "8":
            # Run everything
            file_path = select_results_file(results_manager)
            if file_path:
                try:
                    console.print()
                    print_success(f"Running all analysis features for: {file_path}")
                    console.print()
                    
                    from paperpilot.cli.app import everything
                    everything(str(file_path))
                except KeyboardInterrupt:
                    console.print()
                    print_error("Everything mode cancelled by user")
                except Exception as e:
                    print_error(f"Everything mode failed: {e}")
        
        elif choice == "9":
            # Exit
            console.print()
            print_success("Goodbye!")
            break
        
        # Pause before showing menu again
        if choice != "9":
            console.print()
            Prompt.ask("[dim]Press Enter to continue...[/dim]", default="")


if __name__ == "__main__":
    run_interactive()
