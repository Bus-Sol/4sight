/** @odoo-module */

import { registry } from "@web/core/registry"
import { KpiCard } from "./kpi_card/kpi_card"
import { TextCard } from "./text_card/text_card"
import { ChartRenderer } from "./chart_renderer/chart_renderer"
import { loadJS } from "@web/core/assets"
import { useService } from "@web/core/utils/hooks"
const { Component, onWillStart, useRef, onMounted, useState } = owl
import { getColor } from "@web/core/colors/colors"
import { browser } from "@web/core/browser/browser"
import { routeToUrl } from "@web/core/browser/router_service"
import { jsonrpc } from "@web/core/network/rpc_service";


export class OwlProjectDashboard extends Component {

    // tasks by stage
    async getTasksByStage(){
        let domain = [['project_id', '!=', false]]
        if (this.state.selected_project != 'all'){
            domain.push(['project_id','=', parseInt(this.state.selected_project)])
        }
        const data = await this.orm.readGroup("project.task", domain, ['stage_id'], ['stage_id'])

        console.log('stage by task ', data)

        this.state.task_stages = {
            data: {
                labels: data.map(d => d.stage_id[1]),
                  datasets: [
                  {
                    label: 'Count',
                    data: data.map(d => d.stage_id_count),
                    hoverOffset: 4,
                    backgroundColor: data.map((_, index) => getColor(index)),
                  }]
            },
            domain,
            label_field: 'stage_id',
        }
    }

    // tasks allocated and remaining
    async getTasksHours(){
        let domain = [['project_id', '!=', false]]
        if (this.state.selected_project != 'all'){
            domain.push(['project_id','=', parseInt(this.state.selected_project)])
        }
        const data = await this.orm.readGroup("report.project.task.user", domain, ['task_id','allocated_hours','remaining_hours'], ['task_id'])

        this.state.task_hours = {
            data: {
                labels: data.map(d => d.task_id[1]),
                  datasets: [
                  {
                    label: 'Allocated Hours',
                    data: data.map(d => d.allocated_hours),
                    hoverOffset: 4,
                    backgroundColor: "rgba(75, 192, 192)",
                  },
                  {
                    label: 'Remaining Hours',
                    data: data.map(d => d.remaining_hours),
                    hoverOffset: 4,
                    backgroundColor: "rgba(255, 99, 132)",
                  }
                  ]
            },
            domain,
            label_field: 'task_id',
        }
    }

    async getEmployeeHours(){
        let domain = [['project_id', '!=', false]]
        if (this.state.selected_project != 'all'){
            domain.push(['project_id','=', parseInt(this.state.selected_project)])
        }
        const data = await this.orm.readGroup("account.analytic.line", domain, ['employee_id','unit_amount'], ['employee_id'], { lazy: false })
        console.log('employee hours', data)

        const labels = [... new Set(data.map(d => d.employee_id[1]))]

        this.state.employee_hours = {
            data: {
                labels: labels,
                  datasets: [
                  {
                    label: 'Recorded Hours',
                    data: data.map(d => d.unit_amount.toFixed(2)),
                    hoverOffset: 4,
                    backgroundColor: data.map((_, index) => getColor(index)),
                  }
                  ]
            },
            domain,
            label_field: 'employee_id',
        }

    }

    // task progress
    async getTasksProgress(){
        let domain = [['project_id', '!=', false]]
        if (this.state.selected_project != 'all'){
            domain.push(['project_id','=', parseInt(this.state.selected_project)])
        }
        const data = await this.orm.readGroup("report.project.task.user", domain, ['task_id','real_progress'], ['task_id'])

        this.state.task_progress = {
            data: {
                labels: data.map(d => d.task_id[1]),
                  datasets: [
                  {
                    label: 'Progress',
                    data: data.map(d => d.real_progress.toFixed(2)),
                    hoverOffset: 4,
                    backgroundColor: data.map((_, index) => getColor(index)),
                  }]
            },
            domain,
            label_field: 'task_id',
        }
    }

    setup(){
        this.state = useState({

            selected_project: 'all',

        })
        this.orm = useService("orm")
        this.actionService = useService("action")

        const old_chartjs = document.querySelector('script[src="/web/static/lib/Chart/Chart.js"]')
        const router = useService("router")

        if (old_chartjs){
            let { search, hash } = router.current
            search.old_chartjs = old_chartjs != null ? "0":"1"
            hash.action = 86
            browser.location.href = browser.location.origin + routeToUrl(router.current)
        }

        onWillStart(async ()=>{
            await this.getTasks()
            await this.getOrders()
            await this.getProjectText()

            await this.getTasksByStage()
            await this.getTasksHours()
            await this.getEmployeeHours()
            await this.getTasksProgress()
        })

        onMounted(this.onMounted);
    }

    async onMounted() {
		this.render_filter();
	}

    async onChangeProject(){
        console.log(this.state.selected_project)
        await this.getTasks()
        await this.getOrders()
        await this.getProjectText()

        await this.getTasksByStage()
        await this.getTasksHours()
        await this.getEmployeeHours()
        await this.getTasksProgress()
    }

     render_filter() {
         jsonrpc('/project/filter').then(function(data) {
			var projects = data[0]
			var employees = data[1]
			console.log(projects)
			$(projects).each(function(project) {
				$('#project_selection').append("<option value=" + projects[project].id + ">" + projects[project].name + "</option>");
			});

		})

	}
    async getOrders(){
        let domain = []
        if (this.state.selected_project != 'all'){
            domain.push(['project_id','=', parseInt(this.state.selected_project)])
        }
        const data = await this.orm.searchRead("project.task", domain, ['sale_order_id', 'sale_line_id'])


        const set_orders = [... new Set(data.filter(d => d.sale_order_id).map(d => d.sale_order_id[0]))]


        console.log('set_orders',set_orders)


        this.state.orders = {
            count: set_orders.length,

        }

    }
    async getTasks(){
        let domain = []
        if (this.state.selected_project != 'all'){
            domain.push(['project_id','=', parseInt(this.state.selected_project)])
        }
        const data = await this.orm.searchCount("project.task", domain)
//        console.log('tasks',data)
        //this.state.quotations.value = data

        //revenues
        const allocated_hours = await this.orm.readGroup("project.task", domain, ["allocated_hours:sum"], [])
        const effective_hours = await this.orm.readGroup("project.task", domain, ["effective_hours:sum"], [])
        const remaining_hours = allocated_hours[0].allocated_hours ? (allocated_hours[0].allocated_hours - effective_hours[0].effective_hours) : 0
        const progress = allocated_hours[0].allocated_hours ? ((allocated_hours[0].allocated_hours - remaining_hours) / allocated_hours[0].allocated_hours) * 100 : 0
        this.state.tasks = {
            count: data,
            allocated: allocated_hours[0].allocated_hours ? `${(this.convertNumToTime(allocated_hours[0].allocated_hours))}` : 0,
            spent: effective_hours[0].effective_hours ? `${(this.convertNumToTime(effective_hours[0].effective_hours))}` : 0,
            remaining: `${(this.convertNumToTime(remaining_hours))}`,
            progress: `${(progress).toFixed(2)}%`,

        }

        //this.env.services.company
    }

    async getProjectText(){
        let domain = []
        if (this.state.selected_project != 'all'){
            domain.push(['id','=', parseInt(this.state.selected_project)])
            const data = await this.orm.searchRead("project.project", domain, ['achievements', 'dependencies','next_deliverables','action_items'])
            console.log('project_text', data)
            this.state.project = {
                achievements: data[0].achievements,
                dependencies: data[0].dependencies,
                next_deliverables: data[0].next_deliverables,
                action_items: data[0].action_items,

            }

        }
        else{

        this.state.project = {
                achievements: 'NA',
                dependencies: 'NA',
                next_deliverables: 'NA',
                action_items: 'NA',

            }

        }



    }

    async viewTasks(){
        let domain = []
        if (this.state.selected_project != 'all'){
            domain.push(['project_id','=', parseInt(this.state.selected_project)])
        }

        let list_view = await this.orm.searchRead("ir.model.data", [['name', '=', 'open_view_all_tasks_list_view']], ['res_id'])

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Tasks",
            res_model: "project.task",
            domain,
            views: [
                [list_view.length > 0 ? list_view[0].res_id : false, "list"],
                [false, "form"],
            ]
        })
    }

    async viewOrders(){

        let domain = []
        if (this.state.selected_project != 'all'){
            domain.push(['project_id','=', parseInt(this.state.selected_project)])
        }
        const data = await this.orm.searchRead("project.task", domain, ['sale_order_id', 'sale_line_id'])

        const set_orders = [... new Set(data.filter(d => d.sale_order_id).map(d => d.sale_order_id[0]))]

        let list_view = await this.orm.searchRead("ir.model.data", [['name', '=', 'view_order_tree']], ['res_id'])

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Orders",
            res_model: "sale.order",
            domain: [["id","in", set_orders]],
            views: [
                [list_view.length > 0 ? list_view[0].res_id : false, "list"],
                [false, "form"],
            ]
        })
    }

    convertNumToTime(number) {
    // Check sign of given number
    var sign = (number >= 0) ? 1 : -1;

    // Set positive value of number of sign negative
    number = number * sign;

    // Separate the int from the decimal part
    var hour = Math.floor(number);
    var decpart = number - hour;

    var min = 1 / 60;
    // Round to nearest minute
    decpart = min * Math.round(decpart / min);

    var minute = Math.floor(decpart * 60) + '';

    // Add padding if need
    if (minute.length < 2) {
    minute = '0' + minute;
    }

    // Add Sign in final result
    sign = sign == 1 ? '' : '-';

    // Return concated hours and minutes
    return sign + hour + ':' + minute;
}


    async viewTimesheet(){

        let domain = [['project_id','!=', false]]
        if (this.state.selected_project != 'all'){
            domain.push(['project_id','=', parseInt(this.state.selected_project)])
        }

        let list_view = await this.orm.searchRead("ir.model.data", [['name', '=', 'timesheet_view_tree_user']], ['res_id'])

        this.actionService.doAction({
            type: "ir.actions.act_window",
            name: "Time sheets",
            res_model: "account.analytic.line",
            domain,
            views: [
                [list_view.length > 0 ? list_view[0].res_id : false, "list"],
                [false, "form"],
            ]
        })
    }
}

OwlProjectDashboard.template = "owl.OwlProjectDashboard"
OwlProjectDashboard.components = { KpiCard, ChartRenderer, TextCard }

registry.category("actions").add("owl.project_dashboard", OwlProjectDashboard)