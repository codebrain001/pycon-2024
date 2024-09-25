import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from req_engineering_project.tools.search_toolset import SearchToolset, PerplexitySearchTool, ArxivSearchTool
from req_engineering_project.tools.query_engine_toolset import QueryEngineToolset


@CrewBase
class ReqEngineeringProjectCrew():
	"""ReqEngineeringProject crew"""
	def __init__(self, model_name, api_key):
		self.model_name = model_name
		self.api_key = api_key
		os.environ["OPENAI_API_KEY"] = self.api_key

		# Initialize the search tools
		self.search_toolset = SearchToolset()
		self.google_search_tool = self.search_toolset.google_search_tool
		self.website_search_tool = self.search_toolset.website_search_tool
		self.perplexity_ai_search_tool = PerplexitySearchTool()
		self.arxiv_search_tool = ArxivSearchTool()

		# Initialize the Query engine tools
		self.input_query_engine_toolset = QueryEngineToolset(
			document_dir=os.path.join(os.path.dirname(__file__), "tools/data/inputs"),
			model_name=self.model_name,
			api_key=self.api_key,
			collection_name="input_meeting_notes",
			load_collection_status=True
		)
		self.input_summary_tool, self.input_semantic_search_tool = self.input_query_engine_toolset.create_tools()

		self.gdpr_query_engine_toolset = QueryEngineToolset(
			document_dir=os.path.join(os.path.dirname(__file__), "tools/data/compliance_documents"),
			model_name=self.model_name,
			api_key=self.api_key,
			collection_name="gdpr",
			load_collection_status=True
		)
		self.gdpr_summary_tool, self.gdpr_semantic_search_tool = self.gdpr_query_engine_toolset.create_tools()

	@agent
	def meeting_analyst(self) -> Agent:
		return Agent(
			config=self.agents_config['meeting_analyst'],
			verbose=True,
			llm=self.model_name,
			# or running specific agent with different llm 
			# llm = 'gpt-4o-mini',
			tools=[self.input_summary_tool, self.input_semantic_search_tool]
		)
	
	@agent
	def researcher(self) -> Agent:
		return Agent(
			config=self.agents_config['researcher'],
			verbose=True,
			llm=self.model_name,
			tools=[self.google_search_tool, self.arxiv_search_tool, self.perplexity_ai_search_tool, self.website_search_tool]
		)
	
	@agent
	def requirements_developer(self) -> Agent:
		return Agent(
			config=self.agents_config['requirements_developer'],
			verbose=True,
			llm=self.model_name,
		)
	

	@agent
	def compliance_specialist(self) -> Agent:
		return Agent(
			config=self.agents_config['compliance_specialist'],
			verbose=True,
			llm=self.model_name,
			tools=[self.gdpr_summary_tool, self.gdpr_semantic_search_tool]
		)
	
	@agent
	def quality_control_analyst(self) -> Agent:
		return Agent(
			config=self.agents_config['quality_control_analyst'],
			verbose=True,
			llm=self.model_name,
		)

	@task
	def meeting_analysis_task(self) -> Task:
		return Task(
			config=self.tasks_config['meeting_analysis_task'],
			output_file='/src/req_engineering_project/tools/data/outputs/meeting_profiling_documents.md'
		)

	@task
	def research_task(self) -> Task:
		return Task(
			config=self.tasks_config['research_task'],
			output_file='/src/req_engineering_project/tools/data/outputs/market_research.md'
		)
	
	@task
	def requirements_development_task(self) -> Task:
		return Task(
			config=self.tasks_config['requirements_development_task'],
			output_file='/src/req_engineering_project/tools/data/outputs/BRD_draft.md'
		)

	@task
	def compliance_analysis_task(self) -> Task:
		return Task(
			config=self.tasks_config['compliance_analysis_task'],
			output_file='/src/req_engineering_project/tools/data/outputs/compliance_report.md'
		)
	
	@task
	def quality_assurance_task(self) -> Task:
		return Task(
			config=self.tasks_config['quality_assurance_task'],
			output_file='/src/req_engineering_project/tools/data/outputs/final_BRD.md'
		)

	@crew
	def crew(self) -> Crew:
		"""Creates the ReqEngineeringProject crew"""
		return Crew(
			agents=self.agents, # Automatically created by the @agent decorator
			tasks=self.tasks, # Automatically created by the @task decorator
			process=Process.sequential,
			verbose=True,
			memory=True,
			# # For hierarchical process
			# Process=Process.hierarchical,
			# manager_llm='gpt-4o',
			# # Add plaaning feature
			planning=True,
			planning_llm=self.model_name
		)