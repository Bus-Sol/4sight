/** @odoo-module */

import { registry } from "@web/core/registry"
import { loadJS } from "@web/core/assets"
const { Component, onWillStart, useRef, onMounted, useEffect, onWillUnmount } = owl
import { useService } from "@web/core/utils/hooks"

export class ChartRenderer extends Component {
    setup(){
        this.chartRef = useRef("chart")
        this.actionService = useService("action")

        onWillStart(async ()=>{
            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js")
            //await loadJS("/web/static/lib/Chart/Chart.js")
        })

        useEffect(()=>{
            this.renderChart()
        }, ()=>[this.props.config])

        onMounted(()=>this.renderChart())

        onWillUnmount(()=>{
            if (this.chart){
                this.chart.destroy()
            }
        })
    }

    renderChart(){
        const old_chartjs = document.querySelector('script[src="/web/static/lib/Chart/Chart.js"]')

        if (old_chartjs){
            return
        }
        
        if (this.chart){
            this.chart.destroy()
        }

        this.chart = new Chart(this.chartRef.el,
        {
          type: this.props.type,
          data: this.props.config.data,
          options: {
            responsive: true,
            plugins: {
              legend: {
                position: 'bottom',
              },
              title: {
                display: true,
                text: this.props.title,
                position: 'bottom',
              }
            },
            scales: 'scales' in this.props.config ? this.props.config.scales : {},
          },
        }
      );
    }
}

ChartRenderer.template = "owl.ChartRenderer"