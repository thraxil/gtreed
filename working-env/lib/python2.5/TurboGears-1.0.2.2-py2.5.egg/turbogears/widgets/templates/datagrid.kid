<div xmlns:py="http://purl.org/kid/ns#">
  <table id="${name}" class="grid" cellpadding="0" cellspacing="1" border="0">
    <thead py:if="columns">
      <tr>
          <th py:for="i, col in enumerate(columns)" class="col_${i}">
            ${col.title}
          </th>
      </tr>
    </thead>
    <tr py:for="i, row in enumerate(value)" class="${i%2 and 'odd' or 'even'}">
      <td py:for="col in columns">
        ${col.get_field(row)}
      </td>
    </tr>
  </table>
</div>

