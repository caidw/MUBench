<?php

class DataProcessor {

	private $db;

	function __construct($db){
		$this->db = $db;
	}

	public function getPotentialHitsIndex($table){
		$query = $this->db->getSmallDataPotentialHits($table);
		$hits = [];
		$lastIdentifier = "";
		$currentVersion = "";
		$hit = [];
		foreach($query as $q){
			if($lastIdentifier === ""){
				$hit = [];
				$lastIdentifier = $q['project'];
				$hit['project'] = $q['project'];
			}

			if($lastIdentifier === $q['project'] && $currentVersion != $q['version']){
				$hit['versions'][] = $q['version'];
				$currentVersion = $q['version'];
				$hit['stats'][] = $this->db->getStats($table . "_" . $lastIdentifier . "_" . $currentVersion);
			}
			
			if($lastIdentifier != $q['project'] && $currentVersion != $q['version']){
				$hits[] = $hit;
				$hit = [];
				$hit['project'] = $q['project'];
				$hit['version'][] = $q['version'];
				$lastIdentifier = $q['project'];
				$currentVersion = $q['version'];
			}

			if($lastIdentifier === $q['project'] && $currentVersion === $q['version']){
				$add = true;
				foreach($hit['misuse'][$currentVersion] as $m){
					if($m === $q['misuse']){
						$add = false;
					}
				}
				if($add){
					$hit['misuse'][$currentVersion][] = $q['misuse'];
				}
			}
		}
		$hit['stats'][] = $this->db->getStats($table . "_" . $lastIdentifier . "_" . $currentVersion);
		$hits[] = $hit;
		return $hits;
	}

	
	public function getDatasets($prefix){
		return $this->getPrefixTable($prefix, 1);
	}

	public function getDetectors($prefix){
		return $this->getPrefixTable($prefix, 2);
	}

	public function getPrefixTable($prefix, $suffix){
		$tables = $this->db->getTables();
		$names = array();
		foreach($tables as $t){
			if(substr($t,0,strlen($prefix)) === $prefix){
				$names[] = split('[_]', $t)[$suffix];
			}
		}
		return $names;
	}

}