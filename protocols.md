## PUS integration protocol

Port: 8282

### Control variables
1. `c` - check package: c/barcode/address -> e - No answer, 1 - Ok, 0 - Money is req
2. `i` - save package into robot: i/barcode -> e - server error, 1 - Ok, 0 - some error + /{"status": status, "pin": pin, "info": info}
3. `g` - give to client: g/barcode -> e - error, 1- ok, 0 - error + {"status": status, "info": info}
4. `b` - back to postman: b/barcode -> e - error, 1- ok, 0 - error + {"status": status, "info": info}
5. `s` - send sms about delivery: s/phones[]/pins[]/place/barcodes[]
6. `k` - package is kept by robot: k/phones[]/pins[]/place/barcodes[]

