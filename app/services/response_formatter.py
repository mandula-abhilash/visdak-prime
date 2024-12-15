from typing import List, Dict, Any

class ResponseFormatter:
    @staticmethod
    def format_task_results(results: List[tuple]) -> List[Dict[str, Any]]:
        """
        Format raw database results into structured task dictionaries.
        """
        formatted_results = []
        try:
            for row in results:
                formatted_results.append({
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "priority": row[3],
                    "category": row[4]
                })
        except Exception as e:
            print(f"Error formatting results: {e}")
        return formatted_results

    @staticmethod
    def process_template_variables(template_vars: Dict, results: List[Dict]) -> Dict:
        """Process template variables with actual values."""
        processed_vars = {}
        try:
            for key, value in template_vars.items():
                if isinstance(value, str) and value == "len(results)":
                    processed_vars[key] = len(results)
                else:
                    processed_vars[key] = value
            
            # Ensure count is always present
            if "count" not in processed_vars:
                processed_vars["count"] = len(results)
        except Exception as e:
            print(f"Error processing variables: {e}")
            processed_vars = {"count": len(results)}
            
        return processed_vars

    @staticmethod
    def format_response(template: str, template_vars: Dict, results: List[Dict], query: str) -> Dict[str, Any]:
        """
        Format the final response using the template and variables.
        """
        try:
            # Ensure we have processed variables with count
            vars_dict = ResponseFormatter.process_template_variables(template_vars, results)
            
            # Format response message
            try:
                response_message = template.format(**vars_dict)
            except:
                response_message = f"Found {vars_dict['count']} matching tasks."
            
            return {
                "message": "Query executed successfully",
                "query": query,
                "response": response_message,
                "results": results,
                "count": vars_dict["count"]
            }
        except Exception as e:
            # Ultimate fallback
            count = len(results)
            return {
                "message": "Query executed successfully",
                "query": query,
                "response": f"Found {count} matching tasks.",
                "results": results,
                "count": count
            }