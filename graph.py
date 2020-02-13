import matplotlib.pyplot as plt
import io
import base64
import numpy as np
from matplotlib.ticker import MaxNLocator
from collections import namedtuple

def build_line(x_coordinates,y_coordinates):
	img1=io.BytesIO()
	plt.plot(x_coordinates,y_coordinates)
	plt.xlabel('X-Axis data')
	plt.ylabel('Y-Axis data')
	plt.suptitle('Student Data')
	plt.savefig(img1,format='png')
	img1.seek(0)
	line_url=base64.b64encode(img1.read()).decode()
	plt.close()
	return 'data:image/png;base64,{}'.format(line_url)

def build_bar(means_sub1,means_sub2,means_sub3,means_sub4,means_sub5,
	std_sub1,std_sub2,std_sub3,std_sub4,std_sub5):
	n_groups = 1
	fig, ax = plt.subplots()

	index = np.arange(n_groups)
	bar_width = 0.14

	opacity = 0.4
	error_config = {'ecolor': '0.3'}
	img2=io.BytesIO()

	rects1 = ax.bar(index, means_sub1, bar_width,
                alpha=opacity, color='#0F3AF2',
                yerr=std_sub1, error_kw=error_config,
                label='Subject 1')

	rects2 = ax.bar(index + bar_width, means_sub2, bar_width,
	                alpha=opacity, color='#D81616',
	                yerr=std_sub2, error_kw=error_config,
	                label='Subject 2')

	rects3 = ax.bar(index+bar_width*2, means_sub3, bar_width,
	                alpha=opacity, color='#0A9126',
	                yerr=std_sub3, error_kw=error_config,
	                label='Subject 3')

	rects4 = ax.bar(index+bar_width*3, means_sub4, bar_width,
	                alpha=opacity, color='#D2D816',
	                yerr=std_sub4, error_kw=error_config,
	                label='Subject 4')

	rects5 = ax.bar(index+bar_width*4, means_sub5, bar_width,
	                alpha=opacity, color='#EC0CC9',
	                yerr=std_sub5, error_kw=error_config,
	                label='Subject 5')

	ax.set_xlabel('Semesters')
	ax.set_ylabel('Marks')
	ax.set_title('Student Data')
	ax.set_xticks(index + bar_width / 2)
	ax.set_xticklabels(['year'])
	ax.legend()
	fig.tight_layout()

	plt.savefig(img2,format='png')
	img2.seek(0)
	bar_url=base64.b64encode(img2.read()).decode()
	plt.close()
	return 'data:image/png;base64,{}'.format(bar_url)	

def build_bar_category(Open, SCST, DTNT, OBCSBC, ESBCSBCA, Muslim, Maratha, Other):
	n_groups = 1
	fig, ax = plt.subplots()

	index = np.arange(n_groups)
	bar_width = 0.14

	opacity = 0.4
	error_config = {'ecolor': '0.3'}
	img2=io.BytesIO()

	rects1 = ax.bar(index, Open, bar_width,
                alpha=opacity, color='#0F3AF2',
                yerr=0, error_kw=error_config,
                label='Open')

	rects2 = ax.bar(index + bar_width, SCST, bar_width,
	                alpha=opacity, color='#D81616',
	                yerr=0, error_kw=error_config,
	                label='SCST')

	rects3 = ax.bar(index+bar_width*2, DTNT, bar_width,
	                alpha=opacity, color='#0A9126',
	                yerr=0, error_kw=error_config,
	                label='DT&NT')

	rects4 = ax.bar(index+bar_width*3, OBCSBC, bar_width,
	                alpha=opacity, color='#D2D816',
	                yerr=0, error_kw=error_config,
	                label='OBC&SBC')

	rects5 = ax.bar(index+bar_width*3, ESBCSBCA, bar_width,
	                alpha=opacity, color='#FF4000',
	                yerr=0, error_kw=error_config,
	                label='ESBCSBCA')

	rects6 = ax.bar(index+bar_width*4, Muslim, bar_width,
	                alpha=opacity, color='#EC0CC9',
	                yerr=0, error_kw=error_config,
	                label='Muslim')
	
	rects7 = ax.bar(index+bar_width*4, Maratha, bar_width,
	                alpha=opacity, color='#8000FF',
	                yerr=0, error_kw=error_config,
	                label='Maratha')

	rects8 = ax.bar(index+bar_width*4, Other, bar_width,
	                alpha=opacity, color='#EC0CC9',
	                yerr=0, error_kw=error_config,
	                label='Other')

	ax.set_xlabel('Category')
	ax.set_ylabel('Number of students')
	ax.set_title('Students in different Categories')
	ax.set_xticks(index + bar_width*2)
	ax.set_xticklabels([''])
	ax.legend()
	fig.tight_layout()

	plt.savefig(img2,format='png')
	img2.seek(0)
	bar_url=base64.b64encode(img2.read()).decode()
	plt.close()
	return 'data:image/png;base64,{}'.format(bar_url)	


def build_bar_batchwise(comps, it, etrx, extc, mech):
	n_groups = 1
	fig, ax = plt.subplots()

	index = np.arange(n_groups)
	bar_width = 0.14

	opacity = 0.4
	error_config = {'ecolor': '0.3'}
	img2=io.BytesIO()

	rects1 = ax.bar(index, comps, bar_width,
                alpha=opacity, color='#0F3AF2',
                yerr=0, error_kw=error_config,
                label='COMPS')

	rects2 = ax.bar(index + bar_width, it, bar_width,
	                alpha=opacity, color='#D81616',
	                yerr=0, error_kw=error_config,
	                label='IT')

	rects3 = ax.bar(index+bar_width*2, etrx, bar_width,
	                alpha=opacity, color='#0A9126',
	                yerr=0, error_kw=error_config,
	                label='ETRX')

	rects4 = ax.bar(index+bar_width*3, extc, bar_width,
	                alpha=opacity, color='#D2D816',
	                yerr=0, error_kw=error_config,
	                label='EXTC')

	rects5 = ax.bar(index+bar_width*3, mech, bar_width,
	                alpha=opacity, color='#FF4000',
	                yerr=0, error_kw=error_config,
	                label='MECH')



	ax.set_xlabel('Department')
	ax.set_ylabel('Number of students')
	ax.set_title('Students in different Departments')
	ax.set_xticks(index + bar_width)
	ax.set_xticklabels([''])
	ax.legend()
	fig.tight_layout()

	plt.savefig(img2,format='png')
	img2.seek(0)
	bar_url=base64.b64encode(img2.read()).decode()
	plt.close()
	return 'data:image/png;base64,{}'.format(bar_url)	

def build_bar_placement(nd, d, sd):
	n_groups = 1
	fig, ax = plt.subplots()

	index = np.arange(n_groups)
	bar_width = 0.14

	opacity = 0.4
	error_config = {'ecolor': '0.3'}
	img2=io.BytesIO()

	rects1 = ax.bar(index, nd, bar_width,
                alpha=opacity, color='#0F3AF2',
                yerr=0, error_kw=error_config,
                label='Non-Dream')

	rects2 = ax.bar(index + bar_width, d, bar_width,
	                alpha=opacity, color='#D81616',
	                yerr=0, error_kw=error_config,
	                label='Dream')

	rects3 = ax.bar(index+bar_width*2, sd, bar_width,
	                alpha=opacity, color='#0A9126',
	                yerr=0, error_kw=error_config,
	                label='Super-Dream')

	ax.set_xlabel('Company Category')
	ax.set_ylabel('Number of students')
	ax.set_title('Placement Count for different Categories')
	ax.set_xticks(index + bar_width)
	ax.set_xticklabels([''])
	ax.legend()
	fig.tight_layout()

	plt.savefig(img2,format='png')
	img2.seek(0)
	bar_url=base64.b64encode(img2.read()).decode()
	plt.close()
	return 'data:image/png;base64,{}'.format(bar_url)	

def build_pie(labels,sizes,colors,explode): 	
	img3=io.BytesIO()
	plt.pie(sizes,explode=explode,labels=labels,colors=colors,autopct='%1.1f%%',shadow=True,startangle=140)
	plt.suptitle('Student Data')
	plt.savefig(img3,format='png')
	img3.seek(0)
	pie_url=base64.b64encode(img3.read()).decode()
	plt.close()
	return 'data:image/png;base64,{}'.format(pie_url)
