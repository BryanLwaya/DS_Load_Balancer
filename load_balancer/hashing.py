import json
import math
import os

from sortedcontainers import SortedDict


class ConsistentHashing:

    def __init__(self, slots=512, no_of_servers=3):
        self.no_of_servers = no_of_servers
        self.slots = slots
        self.virtual_servers = int(math.log2(slots))
        self.hash_ring = SortedDict()
        self.registered_paths = {}
        self.init_servers()
        self.init_routes()

    # j => is the number of virtual servers per server
    # Hash function to map requests to slots
    def request_hash_fn(self, i):
        # value = (i + (2 * i) + 17) // 2
        value = (i ** 2 + 2 * (i ** 2) + 17 ** 2)
        hash_value = value % self.slots
        return hash_value

    # Hash function to map virtual servers to slots
    def virtual_hashing(self, server_id, virtual_index):
        j = virtual_index
        value = server_id + j + (2 * j) + 25
        hash_value = value % self.slots
        return hash_value

    # Add server to the hash ring
    def add_server_to_ring(self, server_id, hostname):
        if server_id not in self.hash_ring.values():
            try:
                for i in range(self.virtual_servers):
                    server_hash_value = self.virtual_hashing(server_id, i)
                    self.hash_ring[server_hash_value] = (server_id, hostname)

                self.no_of_servers += 1
                print(f"Added server {server_id} with hostname {hostname}")
                print(self.hash_ring)
            except Exception as e:
                return {"message": f"An error occurred while adding server {hostname}: {e}", "status": "failure"}, 500
        else:
            print(f"Server {hostname} already exists in the hash map")

    # Remove server from the hash ring
    def remove_server_from_ring(self, hostname):
        server_id = None
        for key, value in self.hash_ring.items():
            if value[1] == hostname:
                server_id = value[0]
                break
        if server_id is None:
            return {"message": f"Error: Server with hostname {hostname} not found or may have been removed",
                    "status": "failure"}, 404

        to_remove = [slot for slot, value in self.hash_ring.items() if value[0] == server_id]
        for slot in to_remove:
            del self.hash_ring[slot]

        return {"message": f"Server {hostname} removed successfully", "status": "successful"}, 200

    # Get the server for a given request
    def map_request_to_server(self, request_id):
        request_hash_value = self.request_hash_fn(request_id)
        # Find the server with the next highest hash value
        for server_hash, server_id in self.hash_ring.items():
            if server_hash >= request_hash_value:
                return server_id[0]
        # If the request hash value is greater than all server hash values wrap around to the first server
        return self.hash_ring.peekitem(0)[0]

    # in case a server does not respond to heartbeat and needs to be updated
    def update_servers(self, server_id, hostname):
        self.remove_server_from_ring(server_id)
        self.add_server_to_ring(server_id, hostname)
        return self.hash_ring

    # initiating default servers
    def init_servers(self):
        script_dir = os.path.dirname(__file__)
        config_file = os.path.join(script_dir, 'server_configs/default.json')
        try:
            with open(config_file, 'r') as file:
                server_config = json.load(file)
                for server in server_config['servers']:
                    self.add_server_to_ring(server['id'], server['hostname'])
        except FileNotFoundError:
            print("No server configuration file found. Please add servers to the load balancer manually.")
        except json.JSONDecodeError:
            print("Invalid JSON format in the servers configuration file. Please check and try again.")
        except Exception as e:
            print(f"An error occurred while reading the servers configuration file: {e}")

    def init_routes(self):
        # all server routes are to be hashed and registered here (register is through saving in a dictionary)
        self.registered_paths = {
            'home': 'home',
            'heartbeat': 'heartbeat',
            'server_status': 'server_status'
        }
