concat(
  '<table style="border-collapse:collapse;width:100%;font-family:Segoe UI,Arial,sans-serif;font-size:12px;">',
    '<thead>',
      '<tr>',
        '<th style="border-bottom:2px solid #444;padding:6px;text-align:left;">Ítem</th>',
        '<th style="border-bottom:2px solid #444;padding:6px;text-align:left;">Condición</th>',
        '<th style="border-bottom:2px solid #444;padding:6px;text-align:left;">Comentarios</th>',
        '<th style="border-bottom:2px solid #444;padding:6px;text-align:right;">Cantidad</th>',
      '</tr>',
    '</thead>',
    '<tbody>',
      variables('varRows'),
    '</tbody>',
  '</table>'
)