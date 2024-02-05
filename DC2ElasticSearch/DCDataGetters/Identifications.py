
import pudb

import logging, logging.config
logger = logging.getLogger('elastic_indexer')
log_query = logging.getLogger('query')


class Identifications():
	def __init__(self, datagetter):
		self.datagetter = datagetter
		
		self.cur = self.datagetter.cur
		self.con = self.datagetter.con


	def get_data_page(self, page_num):
		if page_num <= self.datagetter.max_page:
			startrow = (page_num - 1) * self.datagetter.pagesize + 1
			lastrow = page_num * self.datagetter.pagesize
			
			
			query = """
			SELECT DISTINCT
			[rownumber],
			idstemp.[idshash] AS [_id],
			i.IdentificationSequence AS IdentificationSequenceID,
			CONVERT(NVARCHAR, i.IdentificationDate, 120) AS [IdentificationDate],
			i.TaxonomicName,
			i.VernacularTerm,
			i.NameURI AS TaxonNameURI,
			i.TypeStatus,
			i.TypeNotes
			FROM [#temp_iu_part_ids] idstemp
			INNER JOIN IdentificationUnit iu 
			ON iu.[CollectionSpecimenID] = idstemp.[CollectionSpecimenID] AND iu.[IdentificationUnitID] = idstemp.[IdentificationUnitID]
			INNER JOIN [Identification] i
			ON i.[CollectionSpecimenID] = iu.[CollectionSpecimenID] AND i.[IdentificationUnitID] = iu.[IdentificationUnitID]
			WHERE idstemp.[rownumber] BETWEEN ? AND ?
			ORDER BY [rownumber], i.[IdentificationSequence]
			;"""
			self.cur.execute(query, [startrow,lastrow])
			#self.columns = [column[0] for column in self.cur.description]
			
			self.rows = self.cur.fetchall()
			self.rows2dicts()
			
			
			return self.identifications_dict, self.flat_identification_fields


	def rows2dicts(self):
		self.identifications_dict = {}
		
		self.flat_identification_fields = {
			'VernacularTerms': {},
			'TypeStatus': {}
		}
		
		for row in self.rows:
			if row[1] not in self.identifications_dict:
				self.identifications_dict[row[1]] = []
			
			identification = {
				'IdentificationSequenceID': row[2],
				'IdentificationDate': row[3],
				'TaxonomicName': row[4],
				'VernacularTerm': row[5],
				'TaxonNameURI': row[6],
				'TypeStatus': row[7],
				'TypeNotes': row[8],
				
			}
			
			self.identifications_dict[row[1]].append(identification)
			
			if row[5] is not None and row[5] != '':
				if row[1] not in self.flat_identification_fields['VernacularTerms']:
					self.flat_identification_fields['VernacularTerms'][row[1]] = []
				
				self.flat_identification_fields['VernacularTerms'][row[1]].append(row[5])
			
			if row[7] is not None and row[7] != '':
				if row[1] not in self.flat_identification_fields['TypeStatus']:
					self.flat_identification_fields['TypeStatus'][row[1]] = []
			
				self.flat_identification_fields['TypeStatus'][row[1]].append(row[7])
			
		return
















