

import os
import networkx as nx
import spacy
import magic

# --- Configuration ---
MARKDOWN_DIR = "markdown_pages"
GRAPH_FILE = "knowledge_graph.gpickle"

# --- Functions ---

def create_knowledge_graph():
    """Creates a knowledge graph from Markdown files."""
    nlp = spacy.load("en_core_web_sm")
    graph = nx.Graph()

    for filename in os.listdir(MARKDOWN_DIR):
        if filename.endswith(".md"):
            filepath = os.path.join(MARKDOWN_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            doc = nlp(content)

            # Add nodes for entities
            for ent in doc.ents:
                graph.add_node(ent.text, label=ent.label_)

            # Add edges for relationships (co-occurrence)
            for sent in doc.sents:
                entities_in_sentence = [ent.text for ent in sent.ents]
                for i in range(len(entities_in_sentence)):
                    for j in range(i + 1, len(entities_in_sentence)):
                        graph.add_edge(entities_in_sentence[i], entities_in_sentence[j])

    nx.write_gpickle(graph, GRAPH_FILE)
    print(f"Knowledge graph created and saved to {GRAPH_FILE}")

def query_knowledge_graph(query):
    """Queries the knowledge graph and returns relevant context."""
    if not os.path.exists(GRAPH_FILE):
        print("Knowledge graph not found. Please create it first.")
        return

    graph = nx.read_gpickle(GRAPH_FILE)
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(query)

    # Find entities in the query
    query_entities = [ent.text for ent in doc.ents]

    if not query_entities:
        print("No entities found in the query.")
        return

    # Find related nodes in the graph
    related_nodes = set()
    for entity in query_entities:
        if entity in graph:
            related_nodes.add(entity)
            related_nodes.update(nx.neighbors(graph, entity))

    if not related_nodes:
        print("No relevant information found in the knowledge graph.")
        return

    # --- Placeholder for LLM ---    
    # In a real application, you would pass this context to an LLM
    # to generate a human-readable answer.
    print("--- Relevant Context ---")
    for node in related_nodes:
        print(f"- {node}")
    print("------------------------")


def main():
    """Main function to run the script."""
    while True:
        print("\n--- GraphRAG Menu ---")
        print("1. Create/Update knowledge graph")
        print("2. Query knowledge graph")
        print("3. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            create_knowledge_graph()
        elif choice == '2':
            query = input("Enter your query: ")
            query_knowledge_graph(query)
        elif choice == '3':
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()

