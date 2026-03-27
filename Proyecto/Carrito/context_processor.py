def total_carrito(request):

    total = 0
    carro = request.session.get("carro", {})
    for value in carro.values():
        total += int(value.get("precio", 0)) * value.get("cantidad", 0)

    return {"total_carro": total}




    
    