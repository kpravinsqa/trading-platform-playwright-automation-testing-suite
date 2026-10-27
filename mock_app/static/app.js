const BRAND = "InvestPro";
const LINKS = [["dashboard", "Portfolio", "dashboard.html"], ["markets", "Markets", "markets.html"],
  ["watchlists", "Watchlists", "watchlists.html"], ["trade", "Trade", "trade.html"], ["orders", "Orders", "orders.html"]];
function shell(active) { if (!requireAuth()) return false; renderShell(active, LINKS, BRAND); return true; }
