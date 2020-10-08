from django.views import View
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from django.views.generic.base import TemplateView
from collections import deque

# approximate time for complete each service in min
CHANGE_OIL_TIME = 2
INFLATE_TIRES_TIME = 5
DIAGNOSTIC = 30

change_oil_queue, inflate_tires_queue, diagnostic_queue = deque(), deque(), deque()
ticket_count = 1
next_ticket = 0  # next ticket to process


class WelcomeView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse('<h2>Welcome to the Hypercar Service!</h2>')


class MenuView(View):
    def get(self, request, *args, **kwargs):
        return render(request, "tickets/menu.html")


class TicketView(TemplateView):
    template_name = "tickets/ticket.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        service = kwargs["service"]
        ticket_num = self.generate_ticket_number(service)
        wait_time = self.count_time(ticket_num)
        context["ticket_num"] = ticket_num
        context["wait_time"] = wait_time
        return context

    def generate_ticket_number(self, service_):
        global ticket_count
        if service_ == "change_oil":
            change_oil_queue.append(ticket_count)
        elif service_ == "inflate_tires":
            inflate_tires_queue.append(ticket_count)
        elif service_ == "diagnostic":
            diagnostic_queue.append(ticket_count)

        ticket_count += 1
        return ticket_count - 1

    def count_time(self, ticket_num_):
        total_time = 0

        for ticket in change_oil_queue:
            if ticket_num_ == ticket:
                return total_time
            total_time += CHANGE_OIL_TIME

        for ticket in inflate_tires_queue:
            if ticket_num_ == ticket:
                return total_time
            total_time += INFLATE_TIRES_TIME

        for ticket in diagnostic_queue:
            if ticket_num_ == ticket:
                return total_time
            total_time += DIAGNOSTIC


class ProcessingView(View):
    def get(self, request):
        context = {
            "oil_queue_len": len(change_oil_queue),
            "inflate_queue_len": len(inflate_tires_queue),
            "diagnostic_queue_len": len(diagnostic_queue)
        }
        return render(request, "tickets/processing.html", context=context)

    def post(self):
        global next_ticket
        next_ticket = self.process_next()
        return redirect("/processing")

    def process_next(self):
        """
        The clients will be served in the following order: first oil change, second tire inflation,
        and finally diagnostic
        """
        return change_oil_queue.popleft() if change_oil_queue else \
            (inflate_tires_queue.popleft() if inflate_tires_queue else
             (diagnostic_queue.popleft() if diagnostic_queue else 0))


class NextView(View):
    def get(self, request):
        return render(request, "tickets/next.html", context={"ticket_num": next_ticket})
