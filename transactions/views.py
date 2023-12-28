from django.db import transaction
from django.http import HttpResponseRedirect
from django.views.generic.edit import FormView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.http import HttpResponse
from django.views.generic import CreateView, ListView
from transactions.constants import DEPOSIT, WITHDRAWAL, LOAN, LOAN_PAID
from datetime import datetime
from django.db.models import Sum
from transactions.forms import (
    DepositForm,
    WithdrawForm,
    LoanRequestForm,
)
from transactions.models import Transaction
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.contrib.auth.models import User
from .forms import ShareMoneyForm


from accounts.models import UserBankAccount as CustomUser

all_users = CustomUser.objects.filter(account_no=10001)
if all_users:
    print('exist')
else:
    print('not exist')


def send_transaction_email(user, to_user, amount, subject, template):
    message = render_to_string(template, {
        'user': user,
        'amount': amount,
    })
    sent_email = EmailMultiAlternatives(
        subject, '', to=[to_user]
    )
    sent_email.attach_alternative(message, 'text/html')
    sent_email.send()


class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account': self.request.user.account
        })
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # template e context data pass kora
        context.update({
            'title': self.title
        })

        return context


# class ShareMoneyView(LoginRequiredMixin, FormView):
#     template_name = 'transactions/share_money.html'
#     title = 'Share Money'
#     success_url = reverse_lazy('home')
#     form_class = ShareMoneyForm

#     def form_valid(self, form):
#         receiver_account_id = form.cleaned_data['account_no']
#         amount_to_transfer = form.cleaned_data['share_money']
#         print(amount_to_transfer, receiver_account_id)

#         sender_user = self.request.user
#         sender_account = sender_user.account

#         receiver_user = get_object_or_404(
#             User, account__id=receiver_account_id)
#         receiver_account = receiver_user.account

#         if sender_account.balance >= amount_to_transfer:
#             sender_account.balance -= amount_to_transfer
#             receiver_account.balance += amount_to_transfer

#             sender_account.save()
#             receiver_account.save()

#             return HttpResponseRedirect(self.get_success_url())
#         form.add_error(None, "Insufficient balance")
#         return self.form_invalid(form)

# class ShareMoneyView(LoginRequiredMixin, CreateView):
    template_name = 'transactions/share_money.html'
    title = 'share money'
    success_url = reverse_lazy('home')
    form_class = ShareMoneyForm

    def form_valid(self, form):
        receiver_account_id = form.cleaned_data['account_no']
        amount_to_transfer = form.cleaned_data['share_money']

        sender_user = self.request.user
        # Assuming the account is associated with a user
        sender_account = sender_user.account

        # Retrieve receiver's account
        receiver_user = get_object_or_404(
            User, account__id=receiver_account_id)
        receiver_account = receiver_user.account

        # Perform the money transfer
        if sender_account.balance >= amount_to_transfer:
            sender_account.balance -= amount_to_transfer
            receiver_account.balance += amount_to_transfer

            sender_account.save()
            receiver_account.save()

            # Redirect to success URL after successful transfer
            return HttpResponseRedirect(self.get_success_url())

        # If the sender does not have sufficient balance
        form.add_error(None, "Insufficient balance")
        return self.form_invalid(form)


class ShareMoneyView(TransactionCreateMixin):
    template_name = 'transactions/share_money.html'
    # title = 'Share Money'
    success_url = reverse_lazy('home')
    form_class = ShareMoneyForm

    def form_valid(self, form):
        print(form)
        receiver_account_id = form.cleaned_data['account_no']
        amount_to_transfer = form.cleaned_data['share_money']
        print(amount_to_transfer, receiver_account_id)
        sender_user = self.request.user
        sender_account = sender_user.account

        receiver_user = get_object_or_404(
            User, account__id=receiver_account_id)
        receiver_account = receiver_user.account

        if sender_account.balance >= amount_to_transfer:
            sender_account.balance -= amount_to_transfer
            receiver_account.balance += amount_to_transfer

            sender_account.save()
            receiver_account.save()

            return super().form_valid(form)
        else:
            form.add_error(None, "Insufficient balance")
            return self.form_invalid(form)


class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit'

    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        # if not account.initial_deposit_date:
        #     now = timezone.now()
        #     account.initial_deposit_date = now
        # amount = 200, tar ager balance = 0 taka new balance = 0+200 = 200
        account.balance += amount
        account.save(
            update_fields=[
                'balance'
            ]
        )

        messages.success(
            self.request,
            f'{"{:,.2f}".format(float(amount))}$ was deposited to your account successfully'
        )

        send_transaction_email(
            self.request.user,
            self.request.user.email,
            amount,
            'Deposit Money Notification',
            'transactions/deposite_email.html'
        )

        return super().form_valid(form)


class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')

        self.request.user.account.balance -= form.cleaned_data.get('amount')
        self.request.user.account.save(update_fields=['balance'])

        messages.success(
            self.request,
            f'Successfully withdrawn {"{:,.2f}".format(float(amount))}$ from your account'
        )
        send_transaction_email(
            self.request.user,
            self.request.user.email,
            amount,
            'Withdraw Money Notification',
            'transactions/withdraw_email.html'
        )
        return super().form_valid(form)


class LoanRequestView(TransactionCreateMixin):
    form_class = LoanRequestForm
    title = 'Request For Loan'

    def get_initial(self):
        initial = {'transaction_type': LOAN}
        return initial

    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        current_loan_count = Transaction.objects.filter(
            account=self.request.user.account, transaction_type=3, loan_approve=True).count()
        if current_loan_count >= 3:
            return HttpResponse("You have cross the loan limits")
        messages.success(
            self.request,
            f'Loan request for {"{:,.2f}".format(float(amount))}$ submitted successfully'
        )
        send_transaction_email(
            self.request.user,
            self.request.user.email,
            amount,
            'Loan Request Notification',
            'transactions/loan_email.html'
        )

        return super().form_valid(form)


class TransactionReportView(LoginRequiredMixin, ListView):
    template_name = 'transactions/transaction_report.html'
    model = Transaction
    balance = 0  # filter korar pore ba age amar total balance ke show korbe

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            account=self.request.user.account
        )
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

            queryset = queryset.filter(
                timestamp__date__gte=start_date, timestamp__date__lte=end_date)
            self.balance = Transaction.objects.filter(
                timestamp__date__gte=start_date, timestamp__date__lte=end_date
            ).aggregate(Sum('amount'))['amount__sum']
        else:
            self.balance = self.request.user.account.balance

        return queryset.distinct()  # unique queryset hote hobe

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account': self.request.user.account
        })

        return context


class PayLoanView(LoginRequiredMixin, View):
    def get(self, request, loan_id):
        loan = get_object_or_404(Transaction, id=loan_id)
        print(loan)
        if loan.loan_approve:
            user_account = loan.account
            # Reduce the loan amount from the user's balance
            # 5000, 500 + 5000 = 5500
            # balance = 3000, loan = 5000
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.loan_approved = True
                loan.transaction_type = LOAN_PAID
                loan.save()
                return redirect('loan_list')
            else:
                messages.error(
                    self.request,
                    f'Loan amount is greater than available balance'
                )

        return redirect('loan_list')


class LoanListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transactions/loan_request.html'
    context_object_name = 'loans'  # loan list ta ei loans context er moddhe thakbe

    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(
            account=user_account, transaction_type=3)
        print(queryset)
        return queryset
