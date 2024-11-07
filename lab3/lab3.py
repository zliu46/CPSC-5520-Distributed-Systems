"""
CPSC 5520, Seattle University

This program detects arbitrage opportunities from real-time Forex quotes
by constructing a currency exchange graph and analyzing it for profitable cycles.

:Authors: Zhou Liu
:Version: f24-02
"""
import socket
import math
import time
from datetime import datetime
from fxp_bytes_subscriber import read_quote, sub_request
from bellman_ford import BellmanFord

EXPIRATION_TIME = 1.5  # seconds for quote expiration

class Subscriber:
    def __init__(self, pub_ip, pub_port, sub_ip, sub_port):
        self.pub_addr = (pub_ip, pub_port)
        self.sub_addr = (sub_ip, sub_port)
        self.graph = {} # Graph storing currency exchange rates as edges
        self.latest_ts = {} # Tracks latest timestamp for each currency pair
        self.cycle = [] # Stores any detected arbitrage cycle

    def subscribe(self):
        """ Sends a subscription request to the Forex publisher. """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            message = sub_request(*self.sub_addr)
            sock.sendto(message, self.pub_addr)
            print(f"Subscribed to {self.pub_addr} from {self.sub_addr}")

    def get_quotes(self):
        """ Listens for incoming quotes from the Forex publisher and processes each quote. """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind(self.sub_addr)
            print(f"Listening on {self.sub_addr}")
            
            while True:
                data, _ = sock.recvfrom(4096)
                for i in range(0, len(data), 32):
                    if len(data[i:i+32]) == 32:
                        self.process_quote(data[i:i+32])
                self.rm_stale_quotes()

    def process_quote(self, quote):
        """ Processes a single quote, updating the graph and checking for arbitrage opportunities. """
        currency1, currency2, rate, ts = read_quote(quote)

        # Ignore out-of-sequence quotes
        if (currency1, currency2) in self.latest_ts and ts <= self.latest_ts[(currency1, currency2)]:
            print(f"{self.format_ts(ts)} {currency1} {currency2} {rate}\n ignoring out-of-sequence message")
            return
        
         # Update timestamp and graph with the new quote
        self.latest_ts[(currency1, currency2)] = ts
        print(f"{self.format_ts(ts)} {currency1} {currency2} {rate}")

        # Convert exchange rate to a negative log weight for arbitrage detection
        self.update_graph(currency1, currency2, -math.log(rate))

        # Check for arbitrage opportunities and report if found
        if self.check_arbitrage():
            self.rept_arbitrage()

    def update_graph(self, currency1, currency2, weight):
        """ Updates the graph with the exchange rate for the given currency pair. """
        self.graph.setdefault(currency1, {})[currency2] = weight
        self.graph.setdefault(currency2, {})[currency1] = -weight

    def check_arbitrage(self):
        """ Runs Bellman-Ford to detect negative cycles (arbitrage opportunities). """
        start_node = next(iter(self.graph))  # Arbitrary start node
        bf = BellmanFord()
        
        # Add edges to the Bellman-Ford instance
        for src, neighbors in self.graph.items():
            for dest, weight in neighbors.items():
                bf.add_edge(src, dest, weight)
        
        # check arbitrage (negative cycles)
        _, predecessors, negative_cycle = bf.shortest_paths(start_node)
        if negative_cycle:
            self.cycle = self.find_cycle(predecessors, negative_cycle[0])
            return True
        return False

    def find_cycle(self, predecessors, start):
        """ Reconstructs a cycle from predecessors if a negative cycle is found. """
        cycle, visited = [], set()
        node = start
        while node and node not in visited:
            visited.add(node)
            node = predecessors.get(node)
        
        if node is None: return []

        cycle_start = node
        while True:
            cycle.append(node)
            node = predecessors[node]
            if node == cycle_start:
                cycle.append(node)
                break
        cycle.reverse()
        return cycle

    def rept_arbitrage(self):
        """ Prints details of an arbitrage opportunity along the cycle. """
        if not self.cycle:
            print("No cycle available.")
            return

        amount = 100
        print("ARBITRAGE:")
        print("\tstart with USD", amount)
        
        for i in range(len(self.cycle) - 1):
            src, dest = self.cycle[i], self.cycle[i + 1]
            if src in self.graph and dest in self.graph[src]:
                rate = math.exp(-self.graph[src][dest])
                amount *= rate
                print(f"\texchange {src} for {dest} at {rate:.4f} --> {dest} {amount:.2f}")
            else:
                print(f"Missing exchange rate for {src} to {dest}. Skipping.")
                return
            
        # Attempt to convert final currency back to USD
        final_currency = self.cycle[-1]
        if final_currency != "USD":
            if "USD" in self.graph.get(final_currency, {}):
                rate = math.exp(-self.graph[final_currency]["USD"])
                amount *= rate
                print(f"\texchange {final_currency} for USD at {rate:.4f} --> USD {amount:.2f}")
            else:
                print(f"Direct conversion from {final_currency} to USD is not available.")
        # else:
        #     print(f"\tCycle returned to USD with a final amount of: USD {amount:.2f}")

    def rm_stale_quotes(self):
        """ Removes stale quotes from the graph based on expiration time. """
        current_time = time.time() * 1_000_000
        to_remove = [(c1, c2) for (c1, c2), t in self.latest_ts.items() if (current_time - t) > EXPIRATION_TIME * 1_000_000]
        
        for currency1, currency2 in to_remove:
            del self.latest_ts[(currency1, currency2)]
            if currency2 in self.graph[currency1]:
                del self.graph[currency1][currency2]
            if currency1 in self.graph[currency2]:
                del self.graph[currency2][currency1]
            print(f"removing stale quote for ('{currency1}', '{currency2}')")


    @staticmethod
    def format_ts(ts):
        """ Formats the timestamp for printing. """
        return datetime.utcfromtimestamp(ts / 1_000_000).strftime('%Y-%m-%d %H:%M:%S.%f')


if __name__ == "__main__":
    pub_ip = '127.0.0.1'
    sub_ip = '127.0.0.1'
    sub_port = 10001

    # Prompt the user for the publisher port
    try:
        pub_port = int(input("Enter the publisher port: "))
    except ValueError:
        print("Invalid port number. Please enter a valid integer.")
        exit(1)

    subscriber = Subscriber(pub_ip, pub_port, sub_ip, sub_port)
    subscriber.subscribe()
    subscriber.get_quotes()

