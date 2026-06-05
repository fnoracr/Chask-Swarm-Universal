"""
chask_graph_memory.py — Memoria de Grafo Relacional
===================================================
Almacena RELACIONES entre entidades (no solo similitud).
Complementa la memoria vectorial de Qdrant.
Persistencia local con NetworkX + JSON.
"""
import os
import json
import networkx as nx
from datetime import datetime

GRAPH_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph_memory.json")


class GraphMemory:
    def __init__(self):
        self.G = nx.DiGraph()
        self.load()

    def add_entity(self, name, entity_type="generic", attrs=None):
        """Anade un nodo al grafo."""
        self.G.add_node(name, type=entity_type, created=datetime.now().isoformat(),
                        **(attrs or {}))
        self.save()
        return True

    def add_relation(self, source, relation, target, attrs=None):
        """Anade una arista dirigida entre dos entidades."""
        if not self.G.has_node(source):
            self.add_entity(source)
        if not self.G.has_node(target):
            self.add_entity(target)
        self.G.add_edge(source, target, relation=relation,
                        created=datetime.now().isoformat(), **(attrs or {}))
        self.save()
        return True

    def get_relations(self, entity, direction="both"):
        """Obtiene todas las relaciones de una entidad."""
        results = []
        if direction in ("out", "both") and self.G.has_node(entity):
            for _, target, data in self.G.out_edges(entity, data=True):
                results.append({"from": entity, "relation": data.get("relation", "?"),
                                "to": target, "direction": "out"})
        if direction in ("in", "both") and self.G.has_node(entity):
            for source, _, data in self.G.in_edges(entity, data=True):
                results.append({"from": source, "relation": data.get("relation", "?"),
                                "to": entity, "direction": "in"})
        return results

    def find_path(self, source, target):
        """Encuentra el camino mas corto entre dos entidades."""
        try:
            path = nx.shortest_path(self.G, source, target)
            edges = []
            for i in range(len(path) - 1):
                data = self.G.get_edge_data(path[i], path[i + 1])
                edges.append({"from": path[i], "relation": data.get("relation", "?"),
                              "to": path[i + 1]})
            return {"path": path, "edges": edges, "length": len(path) - 1}
        except nx.NetworkXNoPath:
            return {"path": [], "edges": [], "length": -1}
        except nx.NodeNotFound:
            return {"path": [], "edges": [], "length": -1}

    def search_entities(self, entity_type=None, keyword=None):
        """Busca entidades por tipo o nombre parcial."""
        results = []
        for node, data in self.G.nodes(data=True):
            if entity_type and data.get("type") != entity_type:
                continue
            if keyword and keyword.lower() not in node.lower():
                continue
            results.append({"name": node, **data})
        return results

    def stats(self):
        """Estadisticas del grafo."""
        return {
            "nodes": self.G.number_of_nodes(),
            "edges": self.G.number_of_edges(),
            "types": list(set(d.get("type", "?") for _, d in self.G.nodes(data=True)))
        }

    def save(self):
        """Persiste el grafo a JSON."""
        data = nx.node_link_data(self.G)
        with open(GRAPH_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def load(self):
        """Carga el grafo desde JSON."""
        if os.path.exists(GRAPH_FILE):
            try:
                with open(GRAPH_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.G = nx.node_link_graph(data, directed=True)
            except:
                self.G = nx.DiGraph()

    def auto_extract(self, description, project=None, files=None):
        """Extrae entidades y relaciones automaticamente de una descripcion de operacion."""
        # Registrar proyecto
        if project:
            self.add_entity(project, "project")

        # Registrar ficheros y relaciones con proyecto
        if files:
            for f in files:
                fname = os.path.basename(f)
                self.add_entity(fname, "file")
                if project:
                    self.add_relation(project, "contains", fname)

        # Registrar herramientas mencionadas
        tools = ["qdrant", "playwright", "telegram", "discord", "docker",
                 "ollama", "uia", "stealth", "watchdog", "browser"]
        for tool in tools:
            if tool in description.lower():
                self.add_entity(tool, "tool")
                if project:
                    self.add_relation(project, "uses", tool)


if __name__ == "__main__":
    import sys
    gm = GraphMemory()
    if len(sys.argv) > 1:
        if sys.argv[1] == "stats":
            print(json.dumps(gm.stats(), indent=2))
        elif sys.argv[1] == "search" and len(sys.argv) > 2:
            results = gm.search_entities(keyword=sys.argv[2])
            for r in results:
                print(f"  {r['name']} ({r.get('type', '?')})")
        elif sys.argv[1] == "relations" and len(sys.argv) > 2:
            rels = gm.get_relations(sys.argv[2])
            for r in rels:
                print(f"  {r['from']} --[{r['relation']}]--> {r['to']}")
    else:
        print(f"Grafo: {gm.stats()}")
        print("Uso: python chask_graph_memory.py stats|search <keyword>|relations <entity>")
