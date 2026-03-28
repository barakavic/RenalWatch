export default function Table({ columns, rows, rowKey }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full border-separate border-spacing-0">
        <thead>
          <tr className="bg-slate-50">
            {columns.map((column) => (
              <th
                key={column.key}
                className="border-b border-slate-200 px-5 py-4 text-left text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 first:rounded-tl-2xl last:rounded-tr-2xl"
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row[rowKey]} className="bg-white transition hover:bg-slate-50/80">
              {columns.map((column) => (
                <td key={column.key} className="border-b border-slate-100 px-5 py-4 align-top text-sm text-slate-700 last:text-right">
                  {column.render ? column.render(row) : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
