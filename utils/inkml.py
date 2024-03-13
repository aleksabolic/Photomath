import xml.etree.ElementTree as ET
import random
import inkml2img as i2i
import sys
import regex as re
from converter import *
class Segment(object):
	__slots__ = ('seg_id', 'label' ,'strkIds', 'href')
	
	def __init__(self, *args):
		if len(args) == 4:
			self.seg_id = args[0]
			self.label = args[1]
			self.strkIds = args[2]
			self.href = args[3]
		else:
			# default constructor
			self.seg_id = "none"
			self.label = ""
			self.strkIds = set([])
			self.href = ""
	
class Inkml(object):
	"""Class to represent an INKML file with strokes, segmentation and labels"""
	__slots__ = ('fileName', 'strokes', 'strkOrder','segments','truth','UI', 'mathml')
	
	NS = {'ns': 'http://www.w3.org/2003/InkML', 'xml': 'http://www.w3.org/XML/1998/namespace'}

	def __init__(self,*args):
		self.fileName = None
		self.strokes = {}
		self.strkOrder = []
		self.segments = {}
		self.truth = ""
		self.UI = ""
		self.mathml = ""
		
		if len(args) == 1:
			self.fileName = args[0]
			self.loadFromFile()
			try:
				self.loadFromFile()
			except AttributeError:
				self.fileName = None
	
	def fixNS(self,ns,att):
		return '{'+Inkml.NS[ns]+'}'+att

	def loadFromFile(self):
		try:
			tree = ET.parse(self.fileName)
			root = tree.getroot()
		except ET.ParseError as e:
			print(f"XML parsing error: {e}")
			return
		for info in root.findall('ns:annotation',namespaces=Inkml.NS):
			if 'type' in info.attrib:
				if info.attrib['type'] == 'truth':
					self.truth = info.text.strip()
				if info.attrib['type'] == 'UI':
					self.UI = info.text.strip()
		for strk in root.findall('ns:trace',namespaces=Inkml.NS):
			self.strokes[strk.attrib['id']] = strk.text.strip()
			self.strkOrder.append(strk.attrib['id'])


		segments = root.find('ns:traceGroup',namespaces=Inkml.NS)
		if segments is None or len(segments) == 0:
			print("No segmentation info")
			return
		# for each segment in document
		for seg in (segments.iterfind('ns:traceGroup',namespaces=Inkml.NS)):
			seg_id = seg.attrib[self.fixNS('xml','id')]
			label = seg.find('ns:annotation',namespaces=Inkml.NS).text
			strkIdsList = set([])
			for t in seg.findall('ns:traceView',namespaces=Inkml.NS):
				strkIdsList.add(t.attrib['traceDataRef'])
			try:
				href = seg.find('ns:annotationXML', namespaces=Inkml.NS).attrib['href']
			except AttributeError:
				print("Attribute error at:" ,self.fileName)
				href = None

			self.segments[seg_id] = Segment(seg_id, label, strkIdsList, href)

		#extract mathml from inkml
		annotation_xml_elements = root.findall("ns:annotationXML", namespaces=Inkml.NS)

		for element in annotation_xml_elements:
			xml_string = ET.tostring(element, encoding="unicode", method="xml")
			xml_string = xml_string.replace('ns0:', '')
			xml_string = xml_string.replace('ns1:', '')
			xml_string = xml_string.replace("<math>", "<math xmlns='http://www.w3.org/1998/Math/MathML'>")
			xml_string = xml_string.replace("""<annotationXML xmlns:ns0="http://www.w3.org/2003/InkML" xmlns:ns1="http://www.w3.org/1998/Math/MathML" type="truth" encoding="Content-MathML">""", '')
			xml_string = xml_string.replace("</annotationXML>", '')
			self.mathml = xml_string

	    #get the truth from mathml 
		modified_mathml = re.sub(r'xml:id="[^"]*"', '', self.mathml)
		self.truth = mathml2latex_yarosh(modified_mathml)
			
	def augmentRandomSymbol(self, otherInkml, n_changes = 1 ,image_w = 380, image_h = 80, padding_x=0, padding_y=0, thickness = 2):
		# cant change '(' , ')', 
		#forbidden_symbols = ['(',')', '-', '+', '=', '\\sin', '\\cos', '\\neq', '\\leq', '\\lt', '\\sqrt', '\\ldots', '\\pm', '\\div', '\\times', '\\sum', '\\log', '\\geq', '\\rightarrow', '\\lim',  '!', '\\int']
		forbidden_symbols = ['(',')', '\\sqrt', '\\ldots', '\\sum', '\\log', '\\rightarrow', '\\lim',  '!', '\\int', '-', '1', 'i']

		#numbers -> numbers
		#symbols -> symbols, numbers
		#operators -> operators
		#trig -> trig
		#comparators -> comparators
		numbers = ['0','2','3','4','5','6','7','8','9']
		symbols  = ['a','b','c','d','e','f','g','h','j','k','l','m','n','o' ,'p','q','r','s','t','u','v','w','x','y','z', 'A', 'B', 'C','D','E','F','G','H','I','J','K','L','M','N','O' ,'P','Q','R','S','T','U','V','W','X','Y','Z', "\\alpha", "\\beta", "\\gamma", "\\infty", "\\theta", "\\pi", "\\phi"]
		operators = ['+', '\\pm', '\\div', '\\times']
		trig = ['\\sin', '\\cos', '\\tan']
		comparators = ['\\neq', '\\leq', '\\lt', '\\geq', '\\gt', '=']

		# find all non forbidden symbols in this file
		valid_segments = []
		for _, seg in self.segments.items():
			if seg.label not in forbidden_symbols:
				valid_segments.append(seg)

		#find all valid segments in otherInkml
		valid_segments_other = []
		for _, seg in otherInkml.segments.items():
			if seg.label not in forbidden_symbols:
				valid_segments_other.append(seg)

		if len(valid_segments) == 0 or len(valid_segments_other) == 0:
			return None
		
		if n_changes > len(valid_segments):
			n_changes = len(valid_segments)

		replacement_segments = []
		modified_strokes = self.strokes.copy()
		for _ in range(n_changes):
			#choose random valid symbol in this inkml
			idx = random.randint(0,len(valid_segments)-1)

			rep_segment = None
			#random.shuffle(valid_segments_other)
			#check if there is a replacment for this symbol in otherInkml
			for segment in valid_segments_other:
				if valid_segments[idx].label in comparators and segment.label in comparators:
					rep_segment = segment
					break
				elif valid_segments[idx].label in operators and segment.label in operators:
					rep_segment = segment
					break
				elif valid_segments[idx].label in trig and segment.label in trig:
					rep_segment = segment
					break
				elif valid_segments[idx].label in numbers and segment.label in numbers:
					rep_segment = segment
					break
				elif (valid_segments[idx].label in symbols and segment.label in symbols) or (valid_segments[idx].label in symbols and segment.label in numbers):
					rep_segment = segment
					break

			if rep_segment is None:
				valid_segments.pop(idx)
				continue

			min_x, min_y, max_x, max_y = sys.maxsize, sys.maxsize , -sys.maxsize-1, -sys.maxsize-1
			#remove strokes that are related to the choosen segment
			for strkId in valid_segments[idx].strkIds:
				del modified_strokes[strkId]

				#find bounding box around segments
				for line in self.strokes[strkId].split(','): 
					x,y = line.strip().split(' ')
					x,y = float(x), float(y)

					min_x = min(min_x, x)
					max_x = max(max_x, x)
					min_y = min(min_y, y)
					max_y = max(max_y, y)

			replacement_segments.append((rep_segment, valid_segments[idx], min_x, min_y, max_x, max_y))
			valid_segments.pop(idx)
			valid_segments_other.remove(rep_segment)

		#extract only the values 
		modified_strokes = [v for k, v in modified_strokes.items()]

		#choose random symbol in other Inkml
		#idx2 = random.randint(0,len(valid_segments_other)-1)

		for rep_segment, _, min_x, min_y, max_x, max_y in replacement_segments:
			#scale strokes of choosen segment in otherInkml to this inkml choosen segments
			new_strokes = [] # [ [(12 44), (32 44), (11 22)], [(12 23), ...] ] each segment is split into tuples of coordinates
			for strkId in rep_segment.strkIds:
				new_strokes.append([(float(f.split()[0]), float(f.split()[1])) for f in otherInkml.strokes[strkId].strip().split(',')])

			sizes = [ len(stroke) for stroke in new_strokes]
			#unpack new_strokes to be able to scale them
			unpacked_strokes = []
			for stroke in new_strokes:
				unpacked_strokes += stroke
				
			unpacked_strokes = i2i.scale_coordinates_box(unpacked_strokes, min_x, max_x, min_y, max_y)
			
			#pack them and add them to modifed_strokes
			index = 0
			for size in sizes:
				stroke_str = ""
				for i in range(size):
					stroke_str += f'{unpacked_strokes[index][0]} {unpacked_strokes[index][1]},'
					index+=1
				#remove last comma 
				stroke_str = stroke_str.rstrip(stroke_str[-1])

				modified_strokes.append(stroke_str)

		#make image of this Inkml, with replaced symbol with one from otherInkml
		img = i2i.create_seg_img(modified_strokes, image_w = image_w, image_h = image_h, padding_x = padding_x, padding_y = padding_y ,thickness = thickness)

		#make modified truth label
		modified_mathml = self.mathml
		
		for rep_segment, source_segment, _,_,_,_ in replacement_segments:
			target_href = source_segment.href
			new_value = rep_segment.label

			pattern = f'xml:id="{target_href}">'
			value_start = modified_mathml.find(pattern)  # Find the starting index of the pattern

			if value_start != -1:
				value_start += len(pattern)  # Move to the end of the pattern

				# Find the position of the next '<' character after the pattern
				value_end = modified_mathml.find('<', value_start)

				if value_end != -1:
					# Extract the part before and after the value you want to replace
					before_value = modified_mathml[:value_start]
					after_value = modified_mathml[value_end:]

					# Replace the value
					modified_mathml = f"{before_value}{new_value}{after_value}"

		#remove all ids
		modified_mathml = re.sub(r'xml:id="[^"]*"', '', modified_mathml)

		latex = mathml2latex_yarosh(modified_mathml)

		return img, latex


	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	
	