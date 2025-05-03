"""Start MCP Hardware server with all components."""

import asyncio
import argparse
import os
import sys
import ssl
import logging
from pathlib import Path
from dotenv import load_dotenv

from unitmcp import MCPServer, PermissionManager
from unitmcp.server import (
    GPIOServer, InputServer, AudioServer, CameraServer
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def generate_ssl_cert(cert_path, key_path, country, state, locality, organization, common_name, expiry_days):
    """Generate SSL certificate and key for secure connections."""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        import datetime
    except ImportError:
        logger.error("cryptography package is required for SSL certificate generation")
        logger.error("Install it with: pip install cryptography")
        return False

    # Create directories if they don't exist
    cert_dir = os.path.dirname(cert_path)
    key_dir = os.path.dirname(key_path)
    Path(cert_dir).mkdir(parents=True, exist_ok=True)
    Path(key_dir).mkdir(parents=True, exist_ok=True)

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Write private key to file
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    # Create certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, country),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, state),
        x509.NameAttribute(NameOID.LOCALITY_NAME, locality),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=int(expiry_days))
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(common_name)]),
        critical=False,
    ).sign(private_key, hashes.SHA256())

    # Write certificate to file
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    logger.info(f"SSL certificate generated: {cert_path}")
    logger.info(f"SSL private key generated: {key_path}")
    return True

def generate_ssh_key(key_path, key_type="rsa", key_bits=4096, passphrase=None, comment=None):
    """Generate SSH key for secure connections."""
    try:
        import paramiko
    except ImportError:
        logger.error("paramiko package is required for SSH key generation")
        logger.error("Install it with: pip install paramiko")
        return False

    # Create directory if it doesn't exist
    key_dir = os.path.dirname(key_path)
    Path(key_dir).mkdir(parents=True, exist_ok=True)

    # Generate key
    if key_type.lower() == "rsa":
        key = paramiko.RSAKey.generate(bits=key_bits)
    elif key_type.lower() == "dsa":
        key = paramiko.DSSKey.generate(bits=key_bits)
    elif key_type.lower() == "ecdsa":
        key = paramiko.ECDSAKey.generate(bits=key_bits)
    elif key_type.lower() == "ed25519":
        key = paramiko.Ed25519Key.generate()
    else:
        logger.error(f"Unsupported key type: {key_type}")
        return False

    # Save private key
    key.write_private_key_file(key_path, password=passphrase)
    
    # Save public key
    with open(f"{key_path}.pub", "w") as f:
        f.write(f"{key.get_name()} {key.get_base64()}")
        if comment:
            f.write(f" {comment}")

    logger.info(f"SSH private key generated: {key_path}")
    logger.info(f"SSH public key generated: {key_path}.pub")
    return True

async def start_server(host="127.0.0.1", port=8888, components=None, ssl_context=None):
    """Start the MCP Hardware server."""
    # Create permission manager
    permission_manager = PermissionManager()

    # Grant default permissions (adjust as needed)
    permission_manager.grant_permission("client_*", "gpio")
    permission_manager.grant_permission("client_*", "input")
    permission_manager.grant_permission("client_*", "audio")
    permission_manager.grant_permission("client_*", "camera")

    # Create main server
    server = MCPServer(host=host, port=port, permission_manager=permission_manager, ssl_context=ssl_context)

    # Register components
    if components is None or "gpio" in components:
        server.register_server("gpio", GPIOServer())
        print("✓ GPIO server registered")

    if components is None or "input" in components:
        server.register_server("input", InputServer())
        print("✓ Input server registered")

    if components is None or "audio" in components:
        server.register_server("audio", AudioServer())
        print("✓ Audio server registered")

    if components is None or "camera" in components:
        server.register_server("camera", CameraServer())
        print("✓ Camera server registered")

    # Start server
    print(f"\nStarting MCP Hardware Server on {host}:{port} {'with SSL' if ssl_context else ''}")
    print("Press Ctrl+C to stop")

    try:
        await server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.stop()

def main():
    """Main entry point for the server."""
    parser = argparse.ArgumentParser(description="Start MCP Hardware Server")
    parser.add_argument("--host", default=os.getenv("SERVER_HOST", "127.0.0.1"), help="Host to bind to")
    parser.add_argument("--port", type=int, default=int(os.getenv("SERVER_PORT", "8888")), help="Port to bind to")
    parser.add_argument("--components", nargs="+", choices=["gpio", "input", "audio", "camera"], 
                        help="Components to enable (default: all)")
    parser.add_argument("--ssl", action="store_true", default=os.getenv("ENABLE_SSL", "false").lower() == "true", 
                        help="Enable SSL/TLS")
    parser.add_argument("--ssl-cert", default=os.getenv("SSL_CERT_PATH", "./certs/server.crt"), 
                        help="Path to SSL certificate")
    parser.add_argument("--ssl-key", default=os.getenv("SSL_KEY_PATH", "./certs/server.key"), 
                        help="Path to SSL private key")
    parser.add_argument("--generate-ssl-cert", action="store_true", 
                        default=os.getenv("SSL_GENERATE_CERT", "false").lower() == "true",
                        help="Generate SSL certificate if it doesn't exist")
    parser.add_argument("--ssh-key", default=os.getenv("SSH_KEY_PATH", "~/.ssh/id_rsa"), 
                        help="Path to SSH private key")
    parser.add_argument("--generate-ssh-key", action="store_true", 
                        default=os.getenv("SSH_GENERATE_KEY", "false").lower() == "true",
                        help="Generate SSH key if it doesn't exist")
    args = parser.parse_args()

    # Set log level from environment
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.getLogger().setLevel(getattr(logging, log_level))

    # Generate SSL certificate if needed
    ssl_context = None
    if args.ssl:
        if args.generate_ssl_cert and (not os.path.exists(args.ssl_cert) or not os.path.exists(args.ssl_key)):
            logger.info("Generating SSL certificate and key...")
            success = generate_ssl_cert(
                args.ssl_cert,
                args.ssl_key,
                os.getenv("SSL_CERT_COUNTRY", "PL"),
                os.getenv("SSL_CERT_STATE", "Mazowieckie"),
                os.getenv("SSL_CERT_LOCALITY", "Warsaw"),
                os.getenv("SSL_CERT_ORGANIZATION", "UnitMCP"),
                os.getenv("SSL_CERT_COMMON_NAME", "unitmcp.local"),
                os.getenv("SSL_CERT_EXPIRY_DAYS", "365")
            )
            if not success:
                logger.error("Failed to generate SSL certificate. Running without SSL.")
                args.ssl = False
        
        if args.ssl:
            try:
                ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ssl_context.load_cert_chain(args.ssl_cert, args.ssl_key)
                logger.info("SSL/TLS enabled")
            except Exception as e:
                logger.error(f"Failed to load SSL certificate: {e}")
                logger.error("Running without SSL")
                ssl_context = None

    # Generate SSH key if needed
    if args.generate_ssh_key and not os.path.exists(os.path.expanduser(args.ssh_key)):
        logger.info("Generating SSH key...")
        success = generate_ssh_key(
            os.path.expanduser(args.ssh_key),
            os.getenv("SSH_KEY_TYPE", "rsa"),
            int(os.getenv("SSH_KEY_BITS", "4096")),
            os.getenv("SSH_KEY_PASSPHRASE", None),
            os.getenv("SSH_KEY_COMMENT", "UnitMCP Server")
        )
        if not success:
            logger.warning("Failed to generate SSH key.")

    # Start the server
    asyncio.run(start_server(args.host, args.port, args.components, ssl_context))

if __name__ == "__main__":
    main()