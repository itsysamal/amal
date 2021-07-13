# from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsxAbstract
from odoo import models, fields
import datetime
import io
import base64
import xlsxwriter
from num2words import num2words


class AnalyticAccountReportFormXls(models.AbstractModel):
    _name = 'report.analytic_account_reports.analytic_form_xls_id'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):

        header_title_format = workbook.add_format({
            'border': 0,
            'border_color': 'white',
            'align': 'center',
            'font_color': '#000000',
            'bold': True,
            'valign': 'vcenter',
            'fg_color': '#FFFFFF'})
        header_title_format.set_text_wrap()
        header_title_format.set_font_size(36)

        header1_format = workbook.add_format({
            'border': 1,
            'border_color': 'black',
            'align': 'center',
            'font_color': 'yellow',
            'bold': True,
            'valign': 'vcenter',
            'fg_color': '#254061'})
        header1_format.set_text_wrap()
        header1_format.set_font_size(16)
        header5_format = workbook.add_format({
            'border': 1,
            'border_color': 'black',
            'align': 'center',
            'font_color': 'yellow',
            'bold': True,
            'valign': 'vcenter',
            'fg_color': '#254061'})
        header5_format.set_text_wrap()
        header5_format.set_font_size(14)
        header2_format = workbook.add_format({
            'border': 1,
            'border_color': 'black',
            'align': 'center',
            'font_color': 'black',
            'bold': True,
            'valign': 'vcenter',
            'fg_color': '#8EB4E3'})
        header2_format.set_text_wrap()
        header2_format.set_font_size(14)
        header3_format = workbook.add_format({
            'border': 1,
            'border_color': 'black',
            'align': 'center',
            'font_color': 'black',
            'bold': True,
            'valign': 'vcenter',
            'fg_color': 'gray'})
        header3_format.set_text_wrap()
        header3_format.set_font_size(14)
        header4_format = workbook.add_format({
            'border': 1,
            'border_color': 'black',
            'align': 'center',
            'font_color': 'white',
            'bold': True,
            'valign': 'vcenter',
            'fg_color': '#FF0000'})
        header4_format.set_text_wrap()
        header4_format.set_font_size(14)
        header6_format = workbook.add_format({
            'border': 1,
            'border_color': 'black',
            'align': 'center',
            'font_color': 'white',
            'bold': True,
            'valign': 'vcenter',
            'fg_color': '#92D050'})
        header6_format.set_text_wrap()
        header6_format.set_font_size(14)
        header7_format = workbook.add_format({
            'border': 1,
            'border_color': 'black',
            'align': 'center',
            'font_color': 'white',
            'bold': True,
            'valign': 'vcenter',
            'fg_color': 'red'})
        header7_format.set_text_wrap()
        header7_format.set_font_size(14)
        worksheet = workbook.add_worksheet('Analytic accounts Report')
        worksheet.set_column('H:H', 30)
        worksheet.set_row(0, 40)
        worksheet.set_row(1, 40)
        worksheet.set_row(2, 40)
        worksheet.merge_range('D3:L3', 'Analytic accounts Report', header_title_format)

        row = 0
        col = 0
        worksheet.set_row(row, 40)
        worksheet.set_row(row + 1, 40)
        worksheet.set_row(row + 2, 40)
        worksheet.set_column(col, col, 30)
        worksheet.set_column(col + 1, col + 1, 40)
        worksheet.set_column(col + 2, col + 2, 15)
        worksheet.set_column(col + 5, col + 5, 30)
        worksheet.set_column(col + 6, col + 6, 30)
        worksheet.set_row(row + 3, 40)
        worksheet.set_row(row + 4, 40)
        worksheet.set_row(row + 5, 30)
        worksheet.set_row(row + 6, 30)
        worksheet.write(row, col, 'QTY PURCHASED', header1_format)
        worksheet.write(row + 1, col, 'QTY SOLD', header1_format)
        worksheet.write(row + 2, col, 'BALANCE', header1_format)
        worksheet.write(row + 3, col, 'رقم العملية', header2_format)
        worksheet.write(row + 4, col, 'Item', header2_format)
        worksheet.write(row + 5, col, 'Supplier', header2_format)
        worksheet.write(row + 6, col, 'Product Category', header2_format)
        all_attributes_header = []
        all_account_expense_collection = []
        all_account_expense_line = []
        all_currency = []
        for rec in lines:
            all_exp = self.env['account.expense.collection'].search(
                [('analytic_account_id', '=', rec.id)])
            for exp in all_exp:
                if exp.account_id not in all_account_expense_collection:
                    all_account_expense_collection.append(exp.account_id)
        for rec in lines:
            all_attributes = self.env['product.template.attribute.line'].search(
                [('product_tmpl_id', '=', rec.product_id.id), ('print_in_analytic_reports', '=', True)])
            for att in all_attributes:
                if att.attribute_id not in all_attributes_header:
                    all_attributes_header.append(att.attribute_id)
        for rec in lines:
            all_currency_obj = self.env["purchase.multi.currency"].search(
                [('analytic_account_id', '=', rec.id)])
            for cur in all_currency_obj:
                if cur.currency_id not in all_currency:
                    all_currency.append(cur.currency_id)
        row = 7
        for x in all_attributes_header:
            worksheet.set_row(row, 30)
            worksheet.write(row, col, x.name, header2_format)
            row += 1
        worksheet.set_row(row, 30)
        worksheet.set_row(row + 1, 30)
        worksheet.set_row(row + 2, 30)
        worksheet.set_row(row + 3, 40)
        worksheet.write(row, col, 'الكمية المشتراه', header2_format)
        worksheet.write(row + 1, col, 'سعر الشراء', header2_format)
        worksheet.write(row + 2, col, 'Currency', header2_format)
        worksheet.write(row + 3, col, 'Purchase Cost', header2_format)
        worksheet.write(row + 4, col, 'Cost Of Revenue', header2_format)

        row += 5
        for x in all_account_expense_collection:
            worksheet.set_row(row, 30)
            worksheet.write(row, col, x.name, header2_format)
            row += 1
        worksheet.set_row(row, 30)
        worksheet.set_row(row + 1, 30)
        worksheet.set_row(row + 2, 30)
        worksheet.set_row(row + 3, 30)
        worksheet.set_row(row + 4, 30)
        worksheet.set_row(row + 5, 30)
        worksheet.write(row, col, 'Total cost of revenue', header3_format)
        worksheet.write(row + 1, col, 'تكلفة الطن Total cost/qty ', header3_format)
        worksheet.write(row + 2, col, 'Revenue', header3_format)
        worksheet.write(row + 3, col, 'Profit', header3_format)
        worksheet.write(row + 4, col, 'ناتج الكمية المباعة ', header3_format)
        worksheet.write(row + 5, col, 'سعر التعادل', header3_format)
        # col = 1
        total_qty_purchased = 0.0
        total_qty_sold = 0.0
        total_balance_so_po = 0.0
        total_cost_revenue = 0.0
        total_cost_purchased = 0.0
        total_total_cost_revenue = 0.0
        total_total_cost_per_qty = 0.0
        total_total_revenue_income_other = 0.0
        total_total_profit = 0.0
        total_total_qty_result = 0.0
        total_total_balance = 0.0
        for rec in lines:
            row = 0
            col = 0
            worksheet.set_row(row + 3, 40)
            worksheet.set_row(row + 4, 40)
            worksheet.set_row(row + 5, 30)
            worksheet.set_row(row + 6, 30)
            worksheet.write(row, col + 1, '%.2f' % rec.qty_purchased, header5_format)
            worksheet.write(row + 1, col + 1, '%.2f' % rec.qty_sold, header5_format)
            worksheet.write(row + 2, col + 1, '%.2f' % rec.balance_so_po, header5_format)
            worksheet.write(row + 3, col + 1, rec.name, header2_format)
            if rec.product_id:
                worksheet.write(row + 4, col + 1, rec.product_id.name, header2_format)
            else:
                worksheet.write(row + 4, col + 1, ' ', header2_format)
            if rec.vendor_id:
                worksheet.write(row + 5, col + 1, rec.vendor_id.name, header2_format)
            else:
                worksheet.write(row + 5, col + 1, ' ', header2_format)
            if rec.pro_category_id:
                worksheet.write(row + 6, col + 1, rec.pro_category_id.name, header2_format)
            else:
                worksheet.write(row + 6, col + 1, ' ', header2_format)

            total_qty_purchased += rec.qty_purchased
            total_qty_sold += rec.qty_sold
            total_balance_so_po += rec.balance_so_po
            row = 7
            if all_attributes_header:
                for attr in all_attributes_header:
                    worksheet.set_row(row, 30)
                    values = []
                    for pro in rec.product_template_attribute_value_ids:
                        if pro.attribute_id == attr:
                            values.append(pro.product_attribute_value_id.name)
                    if values:
                        worksheet.write(row, col + 1, (', '.join(values)), header2_format)
                    else:
                        worksheet.write(row, col + 1, ' ', header2_format)
                    row += 1
                worksheet.write(row, col + 1, '%.2f' % rec.qty_purchased, header2_format)
            else:
                worksheet.write(row, col + 1, '%.2f' % rec.qty_purchased, header2_format)
            cur_values = []
            cur_name = []
            for cur in rec.po_multi_cur_ids:
                cur_values.append(str('%.2f' % cur.amount))
                cur_name.append(cur.currency_id.name)
            worksheet.set_row(row + 1, 30)
            worksheet.set_row(row + 2, 30)
            if cur_values:
                worksheet.write(row + 1, col + 1, (', '.join(cur_values)), header2_format)
            else:
                worksheet.write(row + 1, col + 1, ' ', header2_format)
            if cur_name:
                worksheet.write(row + 2, col + 1, (', '.join(cur_name)), header2_format)
            else:
                worksheet.write(row + 2, col + 1, ' ', header2_format)
            worksheet.set_row(row + 3, 40)
            worksheet.set_row(row + 4, 30)
            worksheet.write(row + 3, col + 1, '%.2f' % rec.cost_purchased, header2_format)
            worksheet.write(row + 4, col + 1, '%.2f' % rec.cost_revenue, header2_format)
            total_cost_revenue += rec.cost_revenue
            total_cost_purchased += rec.cost_purchased
            # col += 5
            if all_account_expense_collection:
                row += 5
                for exp in all_account_expense_collection:
                    worksheet.set_row(row, 30)
                    values_exp = []
                    for line in rec.account_expense_collection_ids:
                        all_account_expense_line.append(line)
                        if line.account_id == exp and line.account_id.is_expense:
                            values_exp.append(str('%.2f' % line.amount))
                    if values_exp:
                        worksheet.write(row, col + 1, (', '.join(values_exp)), header2_format)
                    else:
                        worksheet.write(row, col + 1, ' ', header2_format)
                    row += 1
                worksheet.set_row(row, 30)
                worksheet.set_row(row + 1, 30)
                worksheet.set_row(row + 2, 30)
                worksheet.set_row(row + 3, 30)
                worksheet.set_row(row + 4, 30)
                worksheet.set_row(row + 5, 30)
                worksheet.write(row, col + 1, '%.2f' % rec.total_cost_revenue, header6_format)
                worksheet.write(row + 1, col + 1, '%.2f' % rec.total_cost_per_qty, header7_format)
                worksheet.write(row + 2, col + 1, '%.2f' % rec.total_revenue_income_other, header6_format)
                worksheet.write(row + 3, col + 1, '%.2f' % rec.total_profit, header3_format)
                worksheet.write(row + 4, col + 1, '%.2f' % rec.total_qty_result, header3_format)
                worksheet.write(row + 5, col + 1, '%.2f' % rec.total_balance, header3_format)
                total_total_cost_revenue += rec.total_cost_revenue
                total_total_cost_per_qty += rec.total_cost_per_qty
                total_total_revenue_income_other += rec.total_revenue_income_other
                total_total_profit += rec.total_profit
                total_total_qty_result += rec.total_qty_result
                total_total_balance += rec.total_balance

            else:
                worksheet.set_row(row + 5, 30)
                worksheet.set_row(row + 6, 30)
                worksheet.set_row(row + 7, 30)
                worksheet.set_row(row + 8, 30)
                worksheet.set_row(row + 9, 30)
                worksheet.set_row(row + 10, 30)
                worksheet.write(row + 5, col + 1, '%.2f' % rec.total_cost_revenue, header6_format)
                worksheet.write(row + 6, col + 1, '%.2f' % rec.total_cost_per_qty, header7_format)
                worksheet.write(row + 7, col + 1, '%.2f' % rec.total_revenue_income_other, header6_format)
                worksheet.write(row + 8, col + 1, '%.2f' % rec.total_profit, header3_format)
                worksheet.write(row + 9, col + 1, '%.2f' % rec.total_qty_result, header3_format)
                worksheet.write(row + 10, col + 1, '%.2f' % rec.total_balance, header3_format)
                total_total_cost_revenue += rec.total_cost_revenue
                total_total_cost_per_qty += rec.total_cost_per_qty
                total_total_revenue_income_other += rec.total_revenue_income_other
                total_total_profit += rec.total_profit
                total_total_qty_result += rec.total_qty_result
                total_total_balance += rec.total_balance
            col += 1
        row = 0
        # worksheet.write(row, col + 1, '%.2f' % total_qty_purchased, header1_format)
        # worksheet.write(row + 1, col + 1, '%.2f' % total_qty_sold, header1_format)
        # worksheet.write(row + 2, col + 1, '%.2f' % total_balance_so_po, header1_format)
        # worksheet.write(row + 3, col + 1, '', header2_format)
        # # worksheet.write(row + 3, col + 1, 'Total', header2_format)
        # worksheet.write(row + 4, col + 1, ' ', header2_format)
        # worksheet.write(row + 5, col + 1, ' ', header2_format)
        # worksheet.write(row + 6, col + 1, ' ', header2_format)
        # row = 7
        # if all_attributes_header:
        #     for attr in all_attributes_header:
        #         worksheet.write(row, col + 1, ' ', header2_format)
        #         row += 1
        #     worksheet.write(row, col + 1, '%.2f' % total_qty_purchased, header1_format)
        # else:
        #     worksheet.write(row, col + 1, '%.2f' % total_qty_purchased, header1_format)
        # worksheet.write(row + 1, col + 1, ' ', header1_format)
        # worksheet.write(row + 2, col + 1, ' ', header1_format)
        # worksheet.write(row + 3, col + 1, '%.2f' % total_cost_purchased, header1_format)
        # worksheet.write(row + 4, col + 1, '%.2f' % total_cost_revenue, header1_format)
        # if all_account_expense_collection:
        #     row += 5
        #     for exp in all_account_expense_collection:
        #         values_exp = []
        #         for line in all_account_expense_line:
        #             if line.account_id == exp and line.account_id.is_expense:
        #                 values_exp.append(line.amount)
        #         if values_exp:
        #             worksheet.write(row, col + 1, sum(values_exp), header1_format)
        #         else:
        #             worksheet.write(row, col + 1, ' ', header1_format)
        #         row += 1
        #     worksheet.write(row, col + 1, total_total_cost_revenue, header1_format)
        #     worksheet.write(row + 1, col + 1, total_total_cost_per_qty, header1_format)
        #     worksheet.write(row + 2, col + 1, total_total_revenue_income_other, header1_format)
        #     worksheet.write(row + 3, col + 1, total_total_profit, header1_format)
        #     worksheet.write(row + 4, col + 1, total_total_qty_result, header1_format)
        #     worksheet.write(row + 5, col + 1, total_total_balance, header1_format)
        # else:
        #     worksheet.write(row + 5, col + 1, '%.2f' % total_total_cost_revenue, header1_format)
        #     worksheet.write(row + 6, col + 1, '%.2f' % total_total_cost_per_qty, header1_format)
        #     worksheet.write(row + 7, col + 1, '%.2f' % total_total_revenue_income_other, header1_format)
        #     worksheet.write(row + 8, col + 1, '%.2f' % total_total_profit, header1_format)
        #     worksheet.write(row + 9, col + 1, '%.2f' % total_total_qty_result, header1_format)
        #     worksheet.write(row + 10, col + 1, '%.2f' % total_total_balance, header1_format)
        row = 4
        worksheet.set_row(row + 4, 30)
        worksheet.set_row(row + 8, 30)
        worksheet.set_row(row + 10, 25)
        worksheet.set_row(row + 11, 25)
        worksheet.set_row(col + 13, 25)
        worksheet.set_row(col + 15, 25)
        worksheet.set_row(col + 16, 25)
        worksheet.set_row(col + 18, 25)
        worksheet.merge_range(row + 4, col + 6, row + 4, col + 7, 'المطلوب فى مراكز التكلفه', header5_format)

        worksheet.merge_range(row + 6, col + 6, row + 6, col + 7, 'قيمة فاتورة الشراء', header4_format)
        worksheet.merge_range(row + 6, col + 3, row + 6, col + 5,
                              'مع ملاحظة انه عند اضافة landed cost  عدم اضافة المصاريف على قيمة المشتريات',
                              header5_format)
        worksheet.merge_range(row + 8, col + 6, row + 8, col + 7, 'مصاريف المشتريات', header4_format)
        worksheet.merge_range(row + 8, col + 3, row + 8, col + 5,
                              'تظهر كما هى فى مركز التكلفه حتى لو تم landed cost عليها بحيث تظهر المصاريف تفصيلا كما هو موضح بالبنود الخاصه بالعملية',
                              header5_format)

        worksheet.merge_range(row + 10, col + 6, row + 10, col + 7, 'المبيعات', header4_format)
        worksheet.merge_range(row + 10, col + 3, row + 10, col + 5,
                              'تظهر بالقيمة الاجمالية على ان يكون هناك اختيار لايضاح تفاصيل فواتير  اذا حدث تعدد فى الفواتير',
                              header1_format)
        worksheet.merge_range(row + 12, col + 6, row + 12, col + 7, 'مطلوب اضافى', header4_format)
        worksheet.merge_range(row + 12, col + 3, row + 12, col + 5,
                              ' ',
                              header5_format)
        worksheet.merge_range(row + 14, col + 6, row + 14, col + 7, 'الكمية من الصنف ', header4_format)
        worksheet.merge_range(row + 14, col + 3, row + 14, col + 5,
                              str('%.2f' % total_balance_so_po) + ' ' + '=' + ' ' + ' رصيد الصنف' + ' ',
                              header5_format)
        worksheet.merge_range(row + 16, col + 6, row + 16, col + 7, 'سعر التعادل', header4_format)
        worksheet.merge_range(row + 16, col + 3, row + 16, col + 5,
                              str('%.2f' % total_total_qty_result) + ' ' + '=' + ' ' + ' قيمة التكاليف الاجمالية - المبيعات / عدد الاطنان المتبيقة من الصنف' + ' ',
                              header5_format)
        worksheet.merge_range(row + 18, col + 6, row + 18, col + 7, 'ناتج الكمية المباعة ', header4_format)
        worksheet.merge_range(row + 18, col + 3, row + 18, col + 5,
                              str('%.2f' % total_total_balance) + ' ' + '=' + ' ' + ' المبيعات - ( الكمية المباعه*تكلفة الطن )' + ' ',
                              header5_format)
        return
