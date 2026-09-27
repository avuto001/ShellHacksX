/*
 * Price chart for the Stock Detail page.
 *
 * Asks Flask for price history (/api/history/<ticker>/<timeframe>) and draws it
 * with Chart.js. Clicking a timeframe button fetches new data and animates the
 * chart to it, with no page reload.
 */
(function () {
  const canvas = document.getElementById("price-chart");
  if (!canvas || !window.Chart) return;

  const COLORS = {
    gain: "#22c55e",
    loss: "#ef4444",
    grid: "rgba(148, 163, 184, 0.08)",
    tick: "#6b7280",
  };

  const chartBox = canvas.parentElement;
  const skeleton = document.getElementById("chart-skeleton");
  const errorBox = document.getElementById("chart-error");
  const periodChange = document.getElementById("period-change");
  const buttons = document.querySelectorAll("[data-timeframe]");
  const historyUrl = canvas.dataset.historyUrl; // contains "__TF__" as a placeholder

  const formatPrice = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

  let chart = null;
  let lineColor = COLORS.gain;
  let latestRequest = 0; // lets us ignore slow responses after a newer click

  Chart.defaults.font.family = "Inter, ui-sans-serif, system-ui, sans-serif";


  // "#22c55e" + 0.3 -> "rgba(34, 197, 94, 0.3)"
  function withOpacity(hex, opacity) {
    const n = parseInt(hex.slice(1), 16);
    return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${opacity})`;
  }

  // Soft fade from the line color down to transparent under the line
  function gradientFill(context) {
    const { ctx, chartArea } = context.chart;
    if (!chartArea) return "transparent"; // chart hasn't been sized yet
    const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
    gradient.addColorStop(0, withOpacity(lineColor, 0.28));
    gradient.addColorStop(1, withOpacity(lineColor, 0));
    return gradient;
  }

  function createChart(labels, prices) {
    chart = new Chart(canvas, {
      type: "line",
      data: {
        labels: labels,
        datasets: [{
          data: prices,
          borderColor: () => lineColor,
          backgroundColor: gradientFill,
          fill: true,
          borderWidth: 2,
          tension: 0.3,
          pointRadius: 0,
          pointHoverRadius: 5,
          pointHoverBackgroundColor: () => lineColor,
          pointHoverBorderColor: "#0b0f19",
          pointHoverBorderWidth: 2,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 600, easing: "easeOutQuart" },
        // Show the tooltip for the nearest date, not only when on the line
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: "#1f2937",
            borderColor: "#374151",
            borderWidth: 1,
            padding: 10,
            displayColors: false,
            titleColor: "#9ca3af",
            titleFont: { weight: "500" },
            bodyColor: "#f9fafb",
            bodyFont: { size: 14, weight: "600" },
            callbacks: {
              label: (item) => formatPrice.format(item.parsed.y),
            },
          },
        },
        scales: {
          x: {
            grid: { display: false },
            border: { display: false },
            ticks: { color: COLORS.tick, maxTicksLimit: 6, maxRotation: 0 },
          },
          y: {
            position: "right",
            grid: { color: COLORS.grid }, // faint horizontal lines only
            border: { display: false },
            ticks: {
              color: COLORS.tick,
              maxTicksLimit: 5,
              callback: (value) => "$" + value.toLocaleString("en-US"),
            },
          },
        },
      },
    });
  }

  function showData(data) {
    const labels = data.points.map((point) => point.date);
    const prices = data.points.map((point) => point.price);

    // Green if the price ended higher than it started, red if lower
    const first = prices[0];
    const last = prices[prices.length - 1];
    const percent = ((last - first) / first) * 100;
    lineColor = percent >= 0 ? COLORS.gain : COLORS.loss;

    periodChange.innerHTML = "";
    const change = document.createElement("span");
    change.className = percent >= 0 ? "text-gain font-semibold" : "text-loss font-semibold";
    change.textContent = `${percent >= 0 ? "+" : ""}${percent.toFixed(2)}%`;
    periodChange.append(change, ` ${data.period_label}`);

    if (!chart) {
      createChart(labels, prices);
    } else {
      chart.data.labels = labels;
      chart.data.datasets[0].data = prices;
      chart.update(); // animates to the new data
    }
  }

  function setActiveButton(timeframe) {
    buttons.forEach((button) => {
      const active = button.dataset.timeframe === timeframe;
      button.setAttribute("aria-pressed", active ? "true" : "false");
      button.classList.toggle("bg-accent", active);
      button.classList.toggle("text-white", active);
      button.classList.toggle("text-gray-400", !active);
      button.classList.toggle("hover:text-gray-200", !active);
    });
  }

  async function loadTimeframe(timeframe) {
    const requestId = ++latestRequest;
    setActiveButton(timeframe);
    errorBox.classList.add("hidden");
    if (chart) chartBox.classList.add("is-loading");
    else skeleton.classList.remove("hidden");

    try {
      const response = await fetch(historyUrl.replace("__TF__", timeframe));
      if (!response.ok) throw new Error(`Server responded with ${response.status}`);
      const data = await response.json();
      if (requestId !== latestRequest) return; // user already clicked something else
      showData(data);
    } catch (error) {
      if (requestId !== latestRequest) return;
      console.error("Failed to load chart data:", error);
      window.StockSense.showError(errorBox, "Couldn't load the chart, try again.", () => loadTimeframe(timeframe));
      errorBox.classList.remove("hidden");
    } finally {
      if (requestId === latestRequest) {
        skeleton.classList.add("hidden");
        chartBox.classList.remove("is-loading");
      }
    }
  }

  buttons.forEach((button) => {
    button.addEventListener("click", () => loadTimeframe(button.dataset.timeframe));
  });

  loadTimeframe(canvas.dataset.defaultTimeframe);
})();
