# lithium-keys
Public license-key registry for Lithium (Minecraft Fabric client).

- keys.json - SHA-256 hashed keys + hwid bindings. No plaintext keys live here.
- Clients verify by hashing the entered key and matching the hwid hash of the machine.
- Bind / reset requests are filed as issues titled LITHIUM-BIND <keyhash> <hwidhash> / LITHIUM-RESET <keyhash> <hwidhash>; the scheduled action processes them, enforces the 24h reset cooldown and closes each request.

Join discord.gg/lithium
