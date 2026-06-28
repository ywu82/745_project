from dnslib import DNSRecord, RR, QTYPE, TXT, A
from socketserver import UDPServer, BaseRequestHandler


class DNSHandler(BaseRequestHandler):
    def handle(self):
        data, socket = self.request
        request = DNSRecord.parse(data)
        print('qname', str(request.q.qname))

        qname = str(request.q.qname)
        qtype = QTYPE[request.q.qtype]

        print(f"[DNS Query] {qtype} {qname}")

        reply = request.reply()
        
        if qtype == "TXT":
            reply.add_answer(
                RR(
                    qname,
                    QTYPE.TXT,
                    rdata=TXT("dGhpcyBpcyBhIHRlc3QgcmVzcG9uc2U="),
                    ttl=60
                )
            )
        else:
            reply.add_answer(
                RR(
                    qname,
                    QTYPE.A,
                    rdata=A("127.0.0.1"),
                    ttl=60
                )
            )

        socket.sendto(reply.pack(), self.client_address)


if __name__ == "__main__":
    server_ip = "0.0.0.0"
    server_port = 5300

    print(f"[INFO] Fake DNS server listening on {server_ip}:{server_port}/UDP")
    server = UDPServer((server_ip, server_port), DNSHandler)
    server.serve_forever()
