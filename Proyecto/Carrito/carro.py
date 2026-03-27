class Carro:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        carro = self.session.get('carro')
        if not carro:
            carro = self.session['carro'] = {}
        self.carro = carro
    
    def agregar(self, producto):
        prod_key = str(producto.id_producto)
        
        if prod_key not in self.carro:
            self.carro[prod_key] = {
                'producto_id': producto.id_producto,
                'nombre': producto.nombre,
                'precio': int(producto.precio),
                'talla': producto.talla,
                'genero': producto.id_genero.nombre_genero,
                'cantidad': 1,
            }
        else:
            
            entry = self.carro[prod_key]
            current = entry.get('cantidad', entry.get('stock_producto', 0))
            if current < producto.stock_producto:
                entry['cantidad'] = current + 1
            else:
                entry['cantidad'] = current  
            if 'stock_producto' in entry:
                entry.pop('stock_producto', None)
        
        self.guardar()
    
    def guardar(self):
        self.session['carro'] = self.carro
        self.session.modified = True
        
    def eliminar(self, producto):
        producto_id = str(producto.id_producto)
        if producto_id in self.carro:
            del self.carro[producto_id]
            self.guardar()
            
            
    def restar(self, producto):
        producto_id = str(producto.id_producto)
        if producto_id in self.carro:
            self.carro[producto_id]['cantidad'] -= 1
            if self.carro[producto_id]['cantidad'] <= 0:
                self.eliminar(producto)
            else:
                self.guardar()
                
    def limpiar(self):
        self.session['carro'] = {}
        self.session.modified = True
        