    if result.from_cache:
        message = "Dados carregados do cache - nenhuma consulta externa foi consumida."
    elif result.lookup_mode in {"closest_projected", "route_projected", "adjacent_date"}:
        message = "Dados previstos carregados com base na malha da companhia para a data informada."
    else:
        message = "Consulta realizada com sucesso via AirLabs."
