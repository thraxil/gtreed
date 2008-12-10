<div xmlns:py="http://purl.org/kid/ns#">
    
  <table>  
    <tr>
        <td>
            <table align="center">
                <tr>
                    <td width="50" align="right">
                        &nbsp;
                        <span py:if="not tg.paginate.current_page == 1">
                            <a href="${tg.paginate.get_href(1)}">&lt;&lt;</a>
                            <a href="${tg.paginate.get_href(tg.paginate.current_page-1)}">&lt;</a>
                        </span>
                    </td>
                    <td>
                        <span py:if="tg.paginate.page_count > 1" py:for="page in tg.paginate.pages">
                            <span py:if="page == tg.paginate.current_page" py:replace="page"/>
                            <span py:if="page != tg.paginate.current_page">
                                <a href="${tg.paginate.get_href(page)}">${page}</a>
                            </span>
                        </span>
                    </td>
                    <td width="50">
                        <span py:if="tg.paginate.pages and not tg.paginate.current_page == tg.paginate.page_count">
                            <a href="${tg.paginate.get_href(tg.paginate.current_page+1)}">&gt;</a>
                            <a href="${tg.paginate.get_href(tg.paginate.page_count)}">&gt;&gt;</a>
                        </span>
                        &nbsp;
                    </td>
                    </tr>    
            </table>        
        </td>
    </tr>
    <tr>
        <td>
          <table id="${name}" class="grid" cellpadding="0" cellspacing="1" border="0">
            <thead py:if="columns">
              <th py:for="i, col in enumerate(columns)" class="col_${i}">
                <a py:if="col.get_option('sortable', False) and getattr(tg, 'paginate', False)" 
                    href="${tg.paginate.get_href(1, col.name, col.get_option('reverse_order', False))}">${col.title}</a>
                <span py:if="not getattr(tg, 'paginate', False) or not col.get_option('sortable', False)" py:replace="col.title"/>
              </th>
            </thead>
            <tr py:for="i, row in enumerate(value)" class="${i%2 and 'odd' or 'even'}">
              <td py:for="col in columns">
                ${col.get_field(row)}
              </td>
            </tr>
          </table>
        </td>
    </tr>
  </table>
</div>

