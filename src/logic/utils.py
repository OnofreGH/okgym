# Prevee que los numeros de celular estén en el formato correcto para WhatsApp
# Normaliza y valida el número al formato peruano con 51
def normalizar_numero(celular):
    try:
        celular = int(float(celular))  # Convierte a int si viene como float
    except (ValueError, TypeError):
        return None

    celular = str(celular)

    if celular.startswith("51") and len(celular) == 11:
        return celular
    elif len(celular) == 9:
        return "51" + celular
    else:
        return None
  